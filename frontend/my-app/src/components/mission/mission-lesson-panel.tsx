"use client";

import * as React from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MissionPlanResponse } from "@/types/mission";

type MissionLessonPanelProps = {
  missionId: string;
};

export default function MissionLessonPanel({ missionId }: MissionLessonPanelProps) {
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);

  React.useEffect(() => {
    const storedPlan = window.sessionStorage.getItem(`mission:${missionId}:plan`);
    if (storedPlan) {
      setPlan(JSON.parse(storedPlan) as MissionPlanResponse);
    }
  }, [missionId]);

  const firstObjective = plan?.objectives[0] ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lesson Workspace</CardTitle>
        <CardDescription>
          Lesson generation starts in the next story. This workspace is ready for the current mission flow.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {firstObjective ? (
          <div className="rounded-md border p-4">
            <p className="text-xs text-muted-foreground">First objective</p>
            <h2 className="mt-1 text-sm font-semibold">{firstObjective.title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{firstObjective.description}</p>
            <p className="mt-3 text-sm">
              <span className="font-medium">Assessment:</span> {firstObjective.assessment_type}
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Generate a mission plan first to preview the first lesson objective here.
          </p>
        )}

        <div className="rounded-md border p-4">
          <p className="text-sm font-medium">Lesson help area</p>
          <p className="mt-2 text-sm text-muted-foreground">
            This panel will become the lesson-specific help and study support area as the lesson flow is built out.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
