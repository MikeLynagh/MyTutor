"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowRight, CheckCircle2, Circle, Loader2, Target, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { MissionProgressResponse, ObjectiveProgress, ObjectiveProgressStatus } from "@/types/mission";
import { missionProgressResponseSchema } from "@/types/mission";

const statusLabel: Record<ObjectiveProgressStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  mastered: "Mastered",
};

const statusClassName: Record<ObjectiveProgressStatus, string> = {
  not_started: "bg-slate-100 text-slate-500",
  in_progress: "bg-indigo-50 text-indigo-700",
  mastered: "bg-emerald-50 text-emerald-700",
};

export default function MissionProgressPage() {
  const params = useParams<{ missionId: string }>();
  const [progress, setProgress] = React.useState<MissionProgressResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

    async function loadProgress() {
      try {
        const response = await fetch(`${apiUrl}/api/missions/${params.missionId}/progress`);
        if (!response.ok) {
          throw new Error(`Failed to load progress: ${response.status}`);
        }

        setProgress(missionProgressResponseSchema.parse(await response.json()));
        setError(null);
      } catch (loadError) {
        console.error("failed to load mission progress", loadError);
        setError("Could not load mission progress.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadProgress();
  }, [params.missionId]);

  if (isLoading) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading progress
        </div>
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="max-w-2xl">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
          <TrendingUp className="h-4 w-4" />
          Progress
        </div>
        <h1 className="text-2xl font-bold text-slate-800">Progress unavailable</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{error}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Button asChild className="bg-indigo-600 hover:bg-indigo-700">
            <Link href={`/missions/${params.missionId}/lesson`}>Go to lesson</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/missions/${params.missionId}/plan`}>Back to plan</Link>
          </Button>
        </div>
      </div>
    );
  }

  const masteredCount = progress.objectives.filter((objective) => objective.status === "mastered").length;
  const attemptedCount = progress.objectives.filter((objective) => objective.attempts > 0).length;

  return (
    <div className="max-w-3xl">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
        <TrendingUp className="h-4 w-4" />
        Progress
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold leading-tight text-slate-800">Mission progress</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Track mastery estimates, focus areas, and the tutor&apos;s current recommendation.
          </p>
        </div>
        <Button asChild className="gap-1 bg-indigo-600 hover:bg-indigo-700">
          <Link href={`/missions/${params.missionId}/lesson`}>
            Continue learning
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      <section className="mt-6 grid gap-3 sm:grid-cols-3">
        <MetricBlock label="Overall mastery" value={`${Math.round(progress.overall_mastery * 100)}%`} />
        <MetricBlock label="Objectives attempted" value={`${attemptedCount}/${progress.objectives.length}`} />
        <MetricBlock label="Objectives mastered" value={`${masteredCount}/${progress.objectives.length}`} />
      </section>

      {progress.current_next_task ? (
        <section className="mt-6 rounded-lg border border-indigo-200 bg-indigo-50/60 px-4 py-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-indigo-600">Current recommendation</p>
              <h2 className="mt-1 text-base font-semibold text-slate-900">{progress.current_next_task.title}</h2>
            </div>
            <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-indigo-700">
              {progress.current_next_task.type.replaceAll("_", " ")}
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-700">{progress.current_next_task.reason}</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{progress.current_next_task.instruction}</p>
        </section>
      ) : (
        <section className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <p className="text-sm font-medium text-slate-800">No recommendation yet</p>
          <p className="mt-1 text-sm leading-relaxed text-slate-600">
            Complete an assessment to let the tutor estimate mastery and recommend the next task.
          </p>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-800">Objectives</h2>
        <div className="mt-4 space-y-3">
          {progress.objectives.map((objective, index) => (
            <ObjectiveProgressItem key={objective.objective_id} objective={objective} index={index} />
          ))}
        </div>
      </section>
    </div>
  );
}

function MetricBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function ObjectiveProgressItem({ objective, index }: { objective: ObjectiveProgress; index: number }) {
  const masteryPercent = Math.round(objective.mastery * 100);

  return (
    <article className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-indigo-600">Lesson {index + 1}</p>
          <h3 className="mt-1 text-base font-semibold text-slate-900">{objective.title}</h3>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClassName[objective.status]}`}>
          {statusLabel[objective.status]}
        </span>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-slate-600">{objective.description}</p>

      <div className="mt-4">
        <div className="flex items-center justify-between gap-3 text-sm">
          <span className="font-medium text-slate-700">Mastery estimate</span>
          <span className="text-slate-500">{masteryPercent}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-indigo-600" style={{ width: `${masteryPercent}%` }} />
        </div>
      </div>

      <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
        <p>
          <span className="font-medium text-slate-800">Attempts:</span> {objective.attempts}
        </p>
        <p>
          <span className="font-medium text-slate-800">Assessment:</span>{" "}
          {objective.assessment_type.replaceAll("_", " ")}
        </p>
      </div>

      {objective.last_feedback ? (
        <div className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm leading-relaxed text-slate-600">
          <span className="font-medium text-slate-800">Latest feedback:</span> {objective.last_feedback}
        </div>
      ) : null}

      {objective.recent_errors.length > 0 ? (
        <div className="mt-4">
          <p className="text-sm font-medium text-slate-800">Focus areas</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            {objective.recent_errors.map((error) => (
              <li key={error} className="flex items-start gap-2">
                <Target className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-4 flex items-center gap-2 text-sm text-slate-500">
          {objective.status === "mastered" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : (
            <Circle className="h-4 w-4 text-slate-300" />
          )}
          No focus areas recorded.
        </p>
      )}
    </article>
  );
}
