"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  FolderOpen,
  Loader2,
  RefreshCcw,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type {
  CuratedResource,
  Mission,
  MissionPlanResponse,
  Objective,
  RejectedResource,
} from "@/types/mission";
import { missionPlanResponseSchema, missionSchema } from "@/types/mission";

function storageKey(missionId: string) {
  return `mission:${missionId}:plan`;
}

function missionStorageKey(missionId: string) {
  return `mission:${missionId}`;
}

export default function MissionPlanPage() {
  const params = useParams<{ missionId: string }>();
  const router = useRouter();
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

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

    const cachedPlan = window.sessionStorage.getItem(storageKey(missionId));
    if (cachedPlan) {
      try {
        setPlan(missionPlanResponseSchema.parse(JSON.parse(cachedPlan)));
      } catch {
        window.sessionStorage.removeItem(storageKey(missionId));
      }
    }

    async function loadWorkspace() {
      try {
        const [missionResponse, planResponse] = await Promise.all([
          fetch(`${apiUrl}/api/missions/${missionId}`),
          fetch(`${apiUrl}/api/missions/${missionId}/plan`),
        ]);

        if (!missionResponse.ok) {
          throw new Error(`Failed to load mission: ${missionResponse.status}`);
        }

        const missionData = missionSchema.parse(await missionResponse.json());
        setMission(missionData);
        window.sessionStorage.setItem(missionStorageKey(missionId), JSON.stringify(missionData));

        if (planResponse.ok) {
          const planData = missionPlanResponseSchema.parse(await planResponse.json());
          setPlan(planData);
          window.sessionStorage.setItem(storageKey(missionId), JSON.stringify(planData));
          setError(null);
        } else if (!cachedPlan) {
          setPlan(null);
          setError("No saved plan was found for this mission yet.");
        }
      } catch (loadError) {
        console.error("failed to load mission workspace", loadError);
        if (!cachedPlan) {
          setError("Could not load mission workspace.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    void loadWorkspace();
  }, [params.missionId]);

  if (isLoading && !plan) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading mission plan
        </div>
      </div>
    );
  }

  if (error && !plan) {
    return (
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-800">Mission plan unavailable</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{error}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Button asChild className="bg-indigo-600 hover:bg-indigo-700">
            <Link href={`/setup/mission/${params.missionId}/plan`}>Generate plan</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/setup">Back to setup</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (!plan) {
    return null;
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
        <Target className="h-4 w-4" />
        Mission plan
      </div>

      <h1 className="text-2xl font-bold leading-tight text-slate-800">
        {mission?.title ?? "Your learning path"}
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-slate-600">
        {mission?.goal ?? "Review the curated resources and objective sequence for this mission."}
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        <Button
          className="gap-1 bg-indigo-600 hover:bg-indigo-700"
          onClick={() => router.push(`/missions/${params.missionId}/lesson`)}
        >
          Start first lesson
          <ArrowRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50"
          onClick={() => {
            window.sessionStorage.removeItem(storageKey(params.missionId));
            router.refresh();
          }}
        >
          <RefreshCcw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      <Separator className="my-8" />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">How this path was built</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <SummaryBlock title="Source summary" text={plan.source_summary} />
          <SummaryBlock
            title="Learning approach"
            text={plan.recommended_learning_approach.replaceAll("_", " ")}
          />
        </div>
      </section>

      <section className="mt-8 space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">Objectives</h2>
        <div className="space-y-3">
          {plan.objectives.map((objective, index) => (
            <ObjectiveItem key={objective.id} objective={objective} index={index} />
          ))}
        </div>
      </section>

      <section className="mt-8 space-y-3">
        <h2 className="text-lg font-semibold text-slate-800">Diagnostic questions</h2>
        <ul className="space-y-2 text-sm text-slate-600">
          {plan.diagnostic_questions.map((question) => (
            <li key={question} className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
              <span>{question}</span>
            </li>
          ))}
        </ul>
      </section>

      <section id="resources" className="mt-10 space-y-4">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-indigo-500" />
          <h2 className="text-lg font-semibold text-slate-800">Resources</h2>
        </div>

        <ResourceList title="Selected resources" resources={plan.selected_sources} />
        {plan.rejected_sources.length > 0 ? (
          <ResourceList title="Rejected resources" resources={plan.rejected_sources} rejected />
        ) : null}
      </section>
    </div>
  );
}

function SummaryBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-sm font-medium text-slate-800">{title}</p>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{text}</p>
    </div>
  );
}

function ObjectiveItem({ objective, index }: { objective: Objective; index: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-indigo-600">
            Lesson {index + 1}
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-800">{objective.title}</h3>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">
          {Math.round(objective.difficulty * 100)}%
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{objective.description}</p>
      <div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
        <p>
          <span className="font-medium text-slate-700">Assessment:</span>{" "}
          {objective.assessment_type.replaceAll("_", " ")}
        </p>
        <p>
          <span className="font-medium text-slate-700">Prerequisites:</span>{" "}
          {objective.prerequisites.length > 0 ? objective.prerequisites.join(", ") : "none"}
        </p>
      </div>
      <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm leading-relaxed text-slate-600">
        <span className="font-medium text-slate-700">Success:</span>{" "}
        {objective.success_criteria}
      </p>
    </div>
  );
}

function ResourceList({
  title,
  resources,
  rejected = false,
}: {
  title: string;
  resources: CuratedResource[] | RejectedResource[];
  rejected?: boolean;
}) {
  if (resources.length === 0) {
    return (
      <div>
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <p className="mt-2 text-sm text-slate-500">No resources to show.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <ul className="mt-3 space-y-2">
        {resources.map((resource) => (
          <li key={`${resource.title}-${resource.url}`} className="rounded-lg border border-slate-200 px-4 py-3">
            <div className="flex items-start gap-2">
              <span
                className={
                  rejected
                    ? "mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full bg-slate-300"
                    : "mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full bg-indigo-400"
                }
              />
              <div className="min-w-0">
                <p className="font-medium text-slate-800">{resource.title}</p>
                <p className="mt-1 break-all text-xs text-slate-400">{resource.url}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{resource.reason}</p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
