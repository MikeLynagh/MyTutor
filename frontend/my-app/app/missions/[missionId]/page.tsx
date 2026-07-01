import { redirect } from "next/navigation";

type MissionRootPageProps = {
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionRootPage({ params }: MissionRootPageProps) {
  const { missionId } = await params;
  redirect(`/missions/${missionId}/plan`);
}
