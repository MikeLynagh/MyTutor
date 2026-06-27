import MissionLessonPanel from "@/components/mission/mission-lesson-panel";

type MissionLessonPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionLessonPage({ params }: MissionLessonPageProps) {
  const { missionId } = await params;
  return <MissionLessonPanel missionId={missionId} />;
}
