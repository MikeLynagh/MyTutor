import MissionProgressPanel from "@/components/mission/mission-progress-panel";

type MissionProgressPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionProgressPage({ params }: MissionProgressPageProps) {
  const { missionId } = await params;
  return <MissionProgressPanel missionId={missionId} />;
}
