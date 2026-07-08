import type { ReactNode } from "react";
import { BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MissionWorkspaceNav } from "@/components/mission/mission-workspace-nav";
import { MissionTutorChat } from "@/components/mission/mission-tutor-chat";

type MissionLayoutProps = {
  children: ReactNode;
  params: Promise<{
    missionId: string;
  }>;
};

export default async function MissionLayout({ children, params }: MissionLayoutProps) {
  const { missionId } = await params;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-50 font-sans">
      <header className="z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-200/80 bg-white/85 px-4 backdrop-blur-sm">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <BookOpen className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-800">
              Teach <span className="text-indigo-600">Workspace</span>
            </p>
            <p className="truncate text-xs text-slate-400">Mission {missionId}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <span className="hidden items-center gap-1.5 sm:flex">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
            Active mission
          </span>
          <Button
            variant="outline"
            size="sm"
            className="hidden border-slate-200 text-slate-600 hover:bg-slate-50 sm:inline-flex"
          >
            Save session
          </Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
        <MissionTutorChat missionId={missionId} />

        <section className="flex min-h-0 flex-1 flex-col bg-white lg:w-[58%]">
          <div className="flex items-center justify-between border-b border-slate-200/80 px-4 py-3 sm:px-6">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Workspace
            </div>
            <MissionWorkspaceNav missionId={missionId} />
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-8 sm:py-6">{children}</div>
        </section>
      </div>
    </div>
  );
}
