"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { answerEvaluationWithMasteryResponse, LessonStartResponse, Mission } from "@/types/mission";
import { answerEvaluationWithMasteryResponseSchema, lessonStartResponseSchema, missionSchema } from "@/types/mission";

function lessonStorageKey(missionId: string) {
  return `mission:${missionId}:lesson`;
}

function missionStorageKey(missionId: string) {
  return `mission:${missionId}`;
}

export default function MissionLessonPage() {
  const params = useParams<{ missionId: string }>();
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [lessonResponse, setLessonResponse] = React.useState<LessonStartResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isRegenerating, setIsRegenerating] = React.useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [answer, setAnswer] = React.useState("");
  const [answerEvaluation, setAnswerEvaluation] = React.useState<answerEvaluationWithMasteryResponse | null>(null);

  React.useEffect(() => {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    const cachedMission = window.sessionStorage.getItem(missionStorageKey(missionId));
    if (cachedMission) {
      try {
        setMission(missionSchema.parse(JSON.parse(cachedMission)));
      } catch {
        window.sessionStorage.removeItem(missionStorageKey(missionId));
      }
    }

    const cachedLesson = window.sessionStorage.getItem(lessonStorageKey(missionId));
    if (cachedLesson) {
      try {
        setLessonResponse(lessonStartResponseSchema.parse(JSON.parse(cachedLesson)));
      } catch {
        window.sessionStorage.removeItem(lessonStorageKey(missionId));
      }
    }

    async function loadLesson() {
      try {
        const [missionResponse, lessonStartResponse] = await Promise.all([
          fetch(`${apiUrl}/api/missions/${missionId}`),
          fetch(`${apiUrl}/api/missions/${missionId}/lessons/start`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          }),
        ]);

        if (!missionResponse.ok) {
          throw new Error(`Failed to load mission: ${missionResponse.status}`);
        }

        const missionData = missionSchema.parse(await missionResponse.json());
        setMission(missionData);
        window.sessionStorage.setItem(missionStorageKey(missionId), JSON.stringify(missionData));

        if (!lessonStartResponse.ok) {
          throw new Error(`Failed to start lesson: ${lessonStartResponse.status}`);
        }

        const lessonData = lessonStartResponseSchema.parse(await lessonStartResponse.json());
        setLessonResponse(lessonData);
        window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
        setError(null);
      } catch (loadError) {
        console.error("failed to load lesson", loadError);
        if (!cachedLesson) {
          setError("Could not load the first lesson for this mission.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    void loadLesson();
  }, [params.missionId]);

  async function regenerateLesson() {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    setIsRegenerating(true);
    try {
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/lessons/start?force=true`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to regenerate lesson: ${response.status}`);
      }

      const lessonData = lessonStartResponseSchema.parse(await response.json());
      setLessonResponse(lessonData);
      setAnswer("");
      setAnswerEvaluation(null);
      window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
      setError(null);
    } catch (regenerateError) {
      console.error("failed to regenerate lesson", regenerateError);
      setError("Could not regenerate the lesson.");
    } finally {
      setIsRegenerating(false);
    }
  }

  async function submitAnswer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!lessonResponse || !answer.trim()) {
      return;
    }

    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    setIsSubmittingAnswer(true);
    setAnswerEvaluation(null);
    try {
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/answers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lesson_id: lessonResponse.lesson.lesson_id,
          objective_id: lessonResponse.lesson.objective_id,
          answer,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit answer: ${response.status}`);
      }

      const evaluation = answerEvaluationWithMasteryResponseSchema.parse(await response.json());
      setAnswerEvaluation(evaluation);
      setError(null);
    } catch (submitError) {
      console.error("failed to submit answer", submitError);
      setError("Could not submit your answer.");
    } finally {
      setIsSubmittingAnswer(false);
    }
  }

  if (isLoading && !lessonResponse) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="size-4 animate-spin" />
          Starting lesson
        </div>
      </div>
    );
  }

  if (error && !lessonResponse) {
    return (
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-800">Lesson unavailable</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{error}</p>
        <Button asChild variant="outline" className="mt-6 border-slate-200 text-slate-600 hover:bg-slate-50">
          <Link href={`/missions/${params.missionId}/plan`}>Back to plan</Link>
        </Button>
      </div>
    );
  }

  if (!lessonResponse) {
    return null;
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
          <span>Lesson 1</span>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 gap-1 border-slate-200 text-xs text-slate-600 hover:bg-slate-50"
          onClick={regenerateLesson}
          disabled={isRegenerating}
        >
          <RefreshCcw className={isRegenerating ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
          Regenerate
        </Button>
      </div>
      <h1 className="mb-4 text-2xl font-bold leading-tight text-slate-800">
        {lessonResponse.lesson.title}
      </h1>
      <p className="mb-6 text-sm italic leading-relaxed text-slate-600">
        Your mission: {mission?.goal ?? "build this skill step by step"}. This lesson covers{" "}
        {lessonResponse.objective_id} and prepares you for the assessment below.
      </p>

      <article
        className="lesson-html"
        dangerouslySetInnerHTML={{ __html: lessonResponse.lesson.lesson_html }}
      />

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-semibold text-slate-800">Key points</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed text-slate-600">
          {lessonResponse.lesson.key_points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      {lessonResponse.lesson.practical_task ? (
        <section className="mt-8">
          <h2 className="mb-2 text-lg font-semibold text-slate-800">Practical task</h2>
          <p className="text-sm leading-relaxed text-slate-600">
            {lessonResponse.lesson.practical_task.instruction}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            <strong className="font-semibold text-slate-800">Success criteria:</strong>{" "}
            {lessonResponse.lesson.practical_task.success_criteria}
          </p>
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-semibold text-slate-800">Assessment</h2>
        <p className="text-sm leading-relaxed text-slate-600">
          {lessonResponse.lesson.assessment.question}
        </p>
      </section>

      <form
        className="mt-6"
        onSubmit={submitAnswer}
      >
        <Textarea
          className="min-h-28 resize-none rounded-lg border-slate-200 text-sm text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-400"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Write your answer here"
        />
        <div className="mt-3 flex justify-end">
          <Button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={!answer.trim() || isSubmittingAnswer}
          >
            {isSubmittingAnswer ? "Submitting..." : "Submit Answer"}
          </Button>
        </div>
      </form>

      {answerEvaluation ? (
        <section className="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-900">Feedback</h2>
            <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600">
              Score {Math.round(answerEvaluation.evaluation.score * 100)}%
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-700">
            {answerEvaluation.evaluation.feedback}
          </p>
          {answerEvaluation.evaluation.misconception ? (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <span className="font-medium text-slate-800">Possible misconception:</span>{" "}
              {answerEvaluation.evaluation.misconception}
            </p>
          ) : null}
          {answerEvaluation.evaluation.missing_points.length > 0 ? (
            <div className="mt-3">
              <p className="text-sm font-medium text-slate-800">Missing points</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
                {answerEvaluation.evaluation.missing_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {answerEvaluation.evaluation.next_hint ? (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <span className="font-medium text-slate-800">Hint:</span>{" "}
              {answerEvaluation.evaluation.next_hint}
            </p>
          ) : null}
          <p className="mt-3 text-sm leading-relaxed text-slate-800">
            <span className="font-medium text-slate-800">Mastery:</span>{' '}
            {Math.round(answerEvaluation.mastery.mastery_before * 100)}% → {Math.round(
              answerEvaluation.mastery.mastery_after * 100,
            )}%
          </p>
        </section>
      ) : null}

      <div className="mt-8 flex items-center justify-between border-t border-slate-200/60 pt-4">
        <Button variant="outline" size="sm" className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50" disabled>
          <ChevronLeft className="h-4 w-4" />
          Previous Lesson
        </Button>
        <span className="text-xs text-slate-400">Lesson 1</span>
        <Button asChild size="sm" className="gap-1 bg-indigo-600 hover:bg-indigo-700">
          <Link href={`/missions/${params.missionId}/progress`}>
            Ready for next lesson
            <ChevronRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
