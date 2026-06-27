import { redirect } from "next/navigation";

type LegacyMissionPlanPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function LegacyMissionPlanPage({ params }: LegacyMissionPlanPageProps) {
  const { missionId } = await params;
  redirect(`/missions/${missionId}/plan`);
}
