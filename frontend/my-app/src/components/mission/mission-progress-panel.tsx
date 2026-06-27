"use client";

import * as React from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MissionPlanResponse } from "@/types/mission";

type MissionProgressPanelProps = {
  missionId: string;
};

export default function MissionProgressPanel({ missionId }: MissionProgressPanelProps) {
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);

  React.useEffect(() => {
    const storedPlan = window.sessionStorage.getItem(`mission:${missionId}:plan`);
    if (storedPlan) {
      setPlan(JSON.parse(storedPlan) as MissionPlanResponse);
    }
  }, [missionId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Progress Workspace</CardTitle>
        <CardDescription>
          Objective-level progress tracking lands in the next story. This route keeps the workspace shape stable now.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {plan?.objectives.length ? (
          plan.objectives.map((objective, index) => (
            <div key={objective.id} className="rounded-md border p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Objective {index + 1}</p>
                  <h2 className="text-sm font-semibold">{objective.title}</h2>
                </div>
                <p className="text-xs text-muted-foreground">Not started</p>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{objective.success_criteria}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">
            Generate a mission plan first to preview progress tracking by objective.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
