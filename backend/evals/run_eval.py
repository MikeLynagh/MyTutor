import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

from cases import CASES, MISSION_PAYLOAD, PLAN_PAYLOAD, EvalCase

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    args = parse_args()
    eval_run_id = args.eval_run_id or f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    db_path = Path(args.db_path) if args.db_path else Path("/tmp") / f"mytutor_{eval_run_id}.sqlite3"
    output_dir = Path(args.output_dir)

    configure_environment(db_path=db_path, real=args.real)

    # Import after environment configuration so app singletons use the eval DB/providers.
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.event_logger import EventLogger

    client = TestClient(app)
    started_at = perf_counter()
    case_results = [run_case(client=client, event_logger=EventLogger(db_path), case=case) for case in CASES]

    summary = build_summary(
        eval_run_id=eval_run_id,
        db_path=db_path,
        provider_mode="real" if args.real else "mock",
        case_results=case_results,
        total_latency_ms=elapsed_ms(started_at),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{eval_run_id}.json"
    md_path = output_dir / f"{eval_run_id}.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")

    print(render_console_summary(summary))
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    return 0 if summary["passed"] == summary["case_count"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repeatable MyTutor adaptive-loop evals.")
    parser.add_argument("--real", action="store_true", help="Use configured real providers instead of mock providers.")
    parser.add_argument("--db-path", help="SQLite path for this eval run. Defaults to /tmp/mytutor_<eval_run_id>.sqlite3.")
    parser.add_argument("--eval-run-id", help="Stable ID for the eval run and output filenames.")
    parser.add_argument(
        "--output-dir",
        default=str(BACKEND_ROOT / "evals" / "outputs"),
        help="Directory for JSON and Markdown eval outputs.",
    )
    return parser.parse_args()


def configure_environment(*, db_path: Path, real: bool) -> None:
    os.environ["MEMORY_DB_PATH"] = str(db_path)
    if not real:
        os.environ["LLM_PROVIDER"] = "mock"
        os.environ["WEB_SEARCH_PROVIDER"] = "mock"
        return

    load_dotenv(BACKEND_ROOT / ".env")
    validate_real_provider_configuration()


def validate_real_provider_configuration() -> None:
    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()
    search_provider = os.getenv("WEB_SEARCH_PROVIDER", "mock").lower()

    if llm_provider == "mock":
        raise RuntimeError("--real requires LLM_PROVIDER to be set to a non-mock provider.")

    if search_provider == "mock":
        raise RuntimeError("--real requires WEB_SEARCH_PROVIDER to be set to a non-mock provider.")

    if llm_provider != "deepseek":
        raise RuntimeError(f"--real does not support LLM_PROVIDER={llm_provider!r} in this app.")

    if search_provider != "exa":
        raise RuntimeError(f"--real does not support WEB_SEARCH_PROVIDER={search_provider!r} in this app.")

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise RuntimeError("--real with LLM_PROVIDER=deepseek requires DEEPSEEK_API_KEY.")

    if not os.getenv("EXA_API_KEY"):
        raise RuntimeError("--real with WEB_SEARCH_PROVIDER=exa requires EXA_API_KEY.")


def run_case(*, client: Any, event_logger: Any, case: EvalCase) -> dict[str, Any]:
    started_at = perf_counter()
    mission_response = assert_response(
        client.post("/api/missions", json=MISSION_PAYLOAD),
        step="create_mission",
        case_name=case.name,
    )
    mission_id = mission_response["id"]

    plan_response = assert_response(
        client.post(f"/api/missions/{mission_id}/plan", json=PLAN_PAYLOAD),
        step="create_plan",
        case_name=case.name,
    )
    objective_id = plan_response["objectives"][0]["id"]

    lesson_response = assert_response(
        client.post(f"/api/missions/{mission_id}/lessons/start"),
        step="start_lesson",
        case_name=case.name,
    )
    lesson = lesson_response["lesson"]

    answer_response = assert_response(
        client.post(
            f"/api/missions/{mission_id}/answers",
            json={
                "lesson_id": lesson["lesson_id"],
                "objective_id": lesson["objective_id"],
                "answer": case.answer,
            },
        ),
        step="submit_answer",
        case_name=case.name,
    )

    # Exercise bounded chat once so chat grounding and event logging are represented in the eval trace.
    chat_response = assert_response(
        client.post(
            f"/api/missions/{mission_id}/chat",
            json={
                "message": "What should I focus on next?",
                "current_objective_id": lesson["objective_id"],
                "history": [],
            },
        ),
        step="chat",
        case_name=case.name,
    )

    events = event_logger.list_events(mission_id=mission_id, limit=100)
    score = answer_response["evaluation"]["score"]
    mastery_before = answer_response["mastery"]["mastery_before"]
    mastery_after = answer_response["mastery"]["mastery_after"]
    actual_next_task_type = answer_response["next_task"]["type"]

    checks = {
        "score_in_expected_range": case.expected_score_min <= score <= case.expected_score_max,
        "next_task_type_expected": actual_next_task_type in case.expected_next_task_types,
        "mastery_direction_expected": mastery_direction_matches(
            expected=case.expected_mastery_direction,
            before=mastery_before,
            after=mastery_after,
        ),
        "required_events_present": required_events_present(events),
        "chat_response_schema_valid": chat_response["message"]["role"] == "assistant"
        and bool(chat_response["message"]["content"].strip()),
    }

    return {
        "case_name": case.name,
        "mission_id": mission_id,
        "objective_id": objective_id,
        "lesson_id": lesson["lesson_id"],
        "pass": all(checks.values()),
        "checks": checks,
        "score": score,
        "is_correct": answer_response["evaluation"]["is_correct"],
        "mastery_before": mastery_before,
        "mastery_after": mastery_after,
        "expected_score_range": [case.expected_score_min, case.expected_score_max],
        "expected_next_task_types": sorted(case.expected_next_task_types),
        "actual_next_task_type": actual_next_task_type,
        "event_count": len(events),
        "event_types": sorted({event.event_type for event in events}),
        "fallback_used": any(event.fallback_used or event.event_type == "fallback_used" for event in events),
        "latency_ms": elapsed_ms(started_at),
    }


def assert_response(response: Any, *, step: str, case_name: str) -> dict[str, Any]:
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"{case_name}:{step} failed with {response.status_code}: {response.text}")

    return response.json()


def required_events_present(events: list[Any]) -> bool:
    event_types = {event.event_type for event in events}
    required = {
        "mission_created",
        "plan_created",
        "lesson_generated",
        "lesson_retrieved",
        "answer_submitted",
        "evaluation_completed",
        "mastery_updated",
        "next_task_selected",
        "chat_response_generated",
    }
    return required.issubset(event_types)


def mastery_direction_matches(*, expected: str, before: float, after: float) -> bool:
    if expected == "increase":
        return after > before

    if expected == "decrease_or_small_increase":
        return after <= before + 0.15

    raise ValueError(f"Unsupported mastery direction expectation: {expected}")


def build_summary(
    *,
    eval_run_id: str,
    db_path: Path,
    provider_mode: str,
    case_results: list[dict[str, Any]],
    total_latency_ms: int,
) -> dict[str, Any]:
    passed = sum(1 for result in case_results if result["pass"])
    event_count = sum(result["event_count"] for result in case_results)
    fallback_count = sum(1 for result in case_results if result["fallback_used"])

    return {
        "eval_run_id": eval_run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "provider_mode": provider_mode,
        "db_path": str(db_path),
        "case_count": len(case_results),
        "passed": passed,
        "failed": len(case_results) - passed,
        "pass_rate": passed / len(case_results) if case_results else 0,
        "fallback_rate": fallback_count / len(case_results) if case_results else 0,
        "total_latency_ms": total_latency_ms,
        "average_case_latency_ms": round(
            sum(result["latency_ms"] for result in case_results) / len(case_results)
            if case_results
            else 0
        ),
        "event_count": event_count,
        "cases": case_results,
    }


def render_console_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"Eval run: {summary['eval_run_id']}",
        f"Provider mode: {summary['provider_mode']}",
        f"Cases: {summary['passed']}/{summary['case_count']} passed",
        f"Fallback rate: {summary['fallback_rate']:.0%}",
        f"Average case latency: {summary['average_case_latency_ms']}ms",
        "",
    ]

    for result in summary["cases"]:
        status = "PASS" if result["pass"] else "FAIL"
        lines.extend(
            [
                f"{status} {result['case_name']}",
                f"  score: {result['score']}",
                f"  mastery: {result['mastery_before']:.2f} -> {result['mastery_after']:.2f}",
                f"  next task: {result['actual_next_task_type']}",
                f"  events: {result['event_count']}",
            ]
        )

    return "\n".join(lines)


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Eval Run {summary['eval_run_id']}",
        "",
        f"- Provider mode: `{summary['provider_mode']}`",
        f"- Cases passed: `{summary['passed']}/{summary['case_count']}`",
        f"- Pass rate: `{summary['pass_rate']:.0%}`",
        f"- Fallback rate: `{summary['fallback_rate']:.0%}`",
        f"- Average case latency: `{summary['average_case_latency_ms']}ms`",
        f"- Event count: `{summary['event_count']}`",
        "",
        "| Case | Result | Score | Mastery | Expected next task | Actual next task | Events |",
        "|---|---:|---:|---:|---|---|---:|",
    ]

    for result in summary["cases"]:
        status = "PASS" if result["pass"] else "FAIL"
        expected_next = ", ".join(result["expected_next_task_types"])
        lines.append(
            f"| `{result['case_name']}` | {status} | {result['score']:.2f} | "
            f"{result['mastery_before']:.2f} -> {result['mastery_after']:.2f} | "
            f"`{expected_next}` | `{result['actual_next_task_type']}` | {result['event_count']} |"
        )

    lines.extend(["", "## Case Checks", ""])
    for result in summary["cases"]:
        lines.append(f"### {result['case_name']}")
        for check_name, passed in result["checks"].items():
            status = "pass" if passed else "fail"
            lines.append(f"- `{check_name}`: {status}")
        lines.append("")

    return "\n".join(lines)


def elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)


if __name__ == "__main__":
    raise SystemExit(main())
