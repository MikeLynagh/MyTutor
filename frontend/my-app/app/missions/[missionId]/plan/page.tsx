import MissionPlanWorkspace from "@/components/mission/mission-plan-workspace";

type MissionPlanPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionPlanPage({ params }: MissionPlanPageProps) {
  const { missionId } = await params;
  return <MissionPlanWorkspace missionId={missionId} />;
}
