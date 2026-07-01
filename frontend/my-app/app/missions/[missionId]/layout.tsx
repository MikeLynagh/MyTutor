import type { ReactNode } from "react";
import {
  BookOpen,
  ChevronDown,
  MessageSquare,
  Send,
  Sparkles,
  User,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { MissionWorkspaceNav } from "@/components/mission/mission-workspace-nav";
import { ScrollArea } from "@/components/ui/scroll-area";

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
        <aside className="flex h-[300px] flex-col border-b border-slate-200/80 bg-white lg:h-auto lg:w-[42%] lg:border-r lg:border-b-0">
          <div className="flex items-center justify-between border-b border-slate-200/80 px-5 py-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-500" />
              <span className="text-sm font-medium text-slate-700">Tutor</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 rounded-full p-0 text-slate-400 hover:text-slate-600"
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>

          <ScrollArea className="flex-1 px-5 py-4">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Avatar className="mt-0.5 h-7 w-7">
                  <AvatarFallback className="bg-indigo-100 text-xs font-medium text-indigo-700">
                    T
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700">Tutor</span>
                    <span className="text-xs text-slate-400">now</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700">
                    <p>
                      Review the plan on the right, then start the first lesson when the sequence
                      looks right.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Avatar className="mt-0.5 h-7 w-7">
                  <AvatarFallback className="bg-slate-200 text-xs font-medium text-slate-600">
                    <User className="h-3.5 w-3.5" />
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700">You</span>
                    <span className="text-xs text-slate-400">mission setup</span>
                  </div>
                  <div className="rounded-lg border border-indigo-200 bg-indigo-50/60 px-4 py-2.5 text-sm font-medium text-indigo-700">
                    Learning path requested
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>

          <div className="border-t border-slate-200/80 bg-white px-4 py-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5">
              <MessageSquare className="h-4 w-4 shrink-0 text-slate-400" />
              <input
                type="text"
                placeholder="Ask about this mission..."
                className="min-w-0 flex-1 border-0 bg-transparent py-1.5 text-sm text-slate-700 outline-none placeholder:text-slate-400"
              />
              <Button size="sm" className="h-7 rounded-md bg-indigo-600 px-3 text-xs text-white hover:bg-indigo-700">
                <Send className="mr-1.5 h-3.5 w-3.5" />
                send
              </Button>
            </div>
          </div>
        </aside>

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
