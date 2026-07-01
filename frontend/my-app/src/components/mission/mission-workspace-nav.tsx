"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, ChevronDown, FolderOpen, LineChart, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const navItems = [
  {
    label: "Lesson",
    segment: "lesson",
    icon: BookOpen,
  },
  {
    label: "Mission",
    segment: "plan",
    icon: Target,
  },
  {
    label: "Resources",
    segment: "resources",
    icon: FolderOpen,
  },
  {
    label: "Progress",
    segment: "progress",
    icon: LineChart,
  },
] as const;

type MissionWorkspaceNavProps = {
  missionId: string;
};

export function MissionWorkspaceNav({ missionId }: MissionWorkspaceNavProps) {
  const pathname = usePathname();
  const activeItem = navItems.find((item) => pathname === `/missions/${missionId}/${item.segment}`) ?? navItems[0];
  const ActiveIcon = activeItem.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50">
          <ActiveIcon className="h-4 w-4" />
          <span>{activeItem.label}</span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {navItems.map((item) => {
          const Icon = item.icon;
          const href = `/missions/${missionId}/${item.segment}`;

          return (
            <DropdownMenuItem key={item.segment} asChild>
              <Link href={href}>
                <Icon className="mr-2 h-4 w-4" />
                {item.label}
              </Link>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
