import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type MissionProgressPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionProgressPage({ params }: MissionProgressPageProps) {
  const { missionId } = await params;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Progress</CardTitle>
        <CardDescription>
          Progress tracking for mission {missionId} will land in the next story.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Button asChild variant="outline">
          <Link href={`/missions/${missionId}/plan`}>Back to plan</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href={`/missions/${missionId}/lesson`}>Go to lesson</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
