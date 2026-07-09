"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FolderOpen, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CuratedResource, MissionPlanResponse, RejectedResource } from "@/types/mission";
import { missionPlanResponseSchema } from "@/types/mission";

function storageKey(missionId: string) {
  return `mission:${missionId}:plan`;
}

export default function MissionResourcesPage() {
  const params = useParams<{ missionId: string }>();
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;
    const cachedPlan = window.sessionStorage.getItem(storageKey(missionId));

    if (cachedPlan) {
      try {
        setPlan(missionPlanResponseSchema.parse(JSON.parse(cachedPlan)));
      } catch {
        window.sessionStorage.removeItem(storageKey(missionId));
      }
    }

    async function loadPlan() {
      try {
        const response = await fetch(`${apiUrl}/api/missions/${missionId}/plan`);
        if (!response.ok) {
          throw new Error(`Failed to load plan: ${response.status}`);
        }

        const planData = missionPlanResponseSchema.parse(await response.json());
        setPlan(planData);
        window.sessionStorage.setItem(storageKey(missionId), JSON.stringify(planData));
        setError(null);
      } catch (loadError) {
        console.error("failed to load resources", loadError);
        if (!cachedPlan) {
          setError("Generate a mission plan before reviewing resources.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    void loadPlan();
  }, [params.missionId]);

  if (isLoading && !plan) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading resources
        </div>
      </div>
    );
  }

  if (error && !plan) {
    return (
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-800">Resources unavailable</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{error}</p>
        <Button asChild className="mt-6 bg-indigo-600 hover:bg-indigo-700">
          <Link href={`/missions/${params.missionId}/plan`}>Back to mission</Link>
        </Button>
      </div>
    );
  }

  if (!plan) {
    return null;
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
        <FolderOpen className="h-4 w-4" />
        Resources
      </div>
      <h1 className="text-2xl font-bold leading-tight text-slate-800">Curated mission resources</h1>
      <p className="mt-3 text-sm leading-relaxed text-slate-600">{plan.source_summary}</p>

      <div className="mt-8 space-y-8">
        <ResourceSection title="Selected resources" resources={plan.selected_sources} />
        {plan.rejected_sources.length > 0 ? (
          <ResourceSection title="Rejected resources" resources={plan.rejected_sources} rejected />
        ) : null}
      </div>
    </div>
  );
}

function ResourceSection({
  title,
  resources,
  rejected = false,
}: {
  title: string;
  resources: CuratedResource[] | RejectedResource[];
  rejected?: boolean;
}) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
      <ul className="mt-3 space-y-3">
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
                <a
                  className="mt-1 block break-all text-xs text-indigo-600 hover:text-indigo-700 hover:underline"
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {resource.url}
                </a>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{resource.reason}</p>
                {"highlights" in resource && resource.highlights.length > 0 ? (
                  <div className="mt-3 rounded-md bg-slate-50 px-3 py-2">
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Source highlights
                    </p>
                    <ul className="mt-2 space-y-1 text-sm leading-relaxed text-slate-600">
                      {resource.highlights.map((highlight) => (
                        <li key={highlight}>{highlight}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
