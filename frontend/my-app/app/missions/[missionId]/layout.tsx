"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Mission, MissionPlanResponse } from "@/types/mission";

type MissionLayoutProps = {
  children: React.ReactNode;
};

const navItems = [
  { label: "Plan", href: "plan" },
  { label: "Lesson", href: "lesson" },
  { label: "Progress", href: "progress" },
] as const;

export default function MissionLayout({ children }: MissionLayoutProps) {
  const params = useParams<{ missionId: string }>();
  const pathname = usePathname();
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);

  React.useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    async function loadWorkspaceData() {
      const storedMission = window.sessionStorage.getItem(`mission:${params.missionId}`);
      if (storedMission) {
        setMission(JSON.parse(storedMission) as Mission);
      }

      const storedPlan = window.sessionStorage.getItem(`mission:${params.missionId}:plan`);
      if (storedPlan) {
        setPlan(JSON.parse(storedPlan) as MissionPlanResponse);
      }

      try {
        const response = await fetch(`${apiUrl.replace(/\/$/, "")}/api/missions/${params.missionId}`);
        if (!response.ok) {
          return;
        }

        const missionResponse: Mission = await response.json();
        setMission(missionResponse);
        window.sessionStorage.setItem(`mission:${params.missionId}`, JSON.stringify(missionResponse));
      } catch (error) {
        console.error("failed to refresh mission workspace data", error);
      }
    }

    void loadWorkspaceData();
  }, [params.missionId]);

  const activeSection = pathname.split("/").pop() ?? "plan";
  const sectionLabel = navItems.find((item) => item.href === activeSection)?.label ?? "Mission";
  const primaryAction =
    activeSection === "plan"
      ? { href: `/missions/${params.missionId}/lesson`, label: "Start First Lesson" }
      : activeSection === "lesson"
        ? { href: `/missions/${params.missionId}/progress`, label: "View Progress" }
        : { href: `/missions/${params.missionId}/lesson`, label: "Return to Lesson" };

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-4 border-b pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Mission Workspace</p>
            <h1 className="text-2xl font-semibold">{mission?.title ?? "Mission"}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span>{mission?.mission_type ?? "Mission type pending"}</span>
              <span>{sectionLabel}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button asChild>
              <Link href={primaryAction.href}>{primaryAction.label}</Link>
            </Button>
          </div>
        </header>

        <nav className="flex flex-wrap gap-2">
          {navItems.map((item) => {
            const href = `/missions/${params.missionId}/${item.href}`;
            const isActive = pathname === href;

            return (
              <Button key={item.href} asChild variant={isActive ? "default" : "outline"}>
                <Link href={href}>{item.label}</Link>
              </Button>
            );
          })}
        </nav>

        <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="min-w-0">{children}</section>

          <aside className="flex flex-col gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Mission Context</CardTitle>
                <CardDescription>Shared context for the current workspace route.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <p className="font-medium">Goal</p>
                  <p className="text-muted-foreground">{mission?.goal ?? "Goal loading..."}</p>
                </div>
                <div>
                  <p className="font-medium">Mission type</p>
                  <p className="text-muted-foreground">{mission?.mission_type ?? "Unknown"}</p>
                </div>
                <div>
                  <p className="font-medium">Current section</p>
                  <p className="text-muted-foreground">{sectionLabel}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Links</CardTitle>
                <CardDescription>Move around the mission without leaving the workspace.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {navItems.map((item) => (
                  <Button key={item.href} asChild variant="outline" className="justify-start">
                    <Link href={`/missions/${params.missionId}/${item.href}`}>{item.label}</Link>
                  </Button>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Mission Snapshot</CardTitle>
                <CardDescription>Current planning context for the mission.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <p className="font-medium">Recommended approach</p>
                  <p className="text-muted-foreground">
                    {plan?.recommended_learning_approach ?? "Generate a plan to see the current approach."}
                  </p>
                </div>
                <div>
                  <p className="font-medium">Objectives</p>
                  <p className="text-muted-foreground">
                    {plan ? `${plan.objectives.length} planned objective${plan.objectives.length === 1 ? "" : "s"}` : "No plan loaded yet"}
                  </p>
                </div>
                <div>
                  <p className="font-medium">Selected resources</p>
                  <p className="text-muted-foreground">
                    {plan ? `${plan.selected_sources.length} selected source${plan.selected_sources.length === 1 ? "" : "s"}` : "No curated sources yet"}
                  </p>
                </div>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </main>
  );
}
