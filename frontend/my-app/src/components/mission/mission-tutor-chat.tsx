"use client";

import * as React from "react";
import { ChevronDown, Loader2, MessageSquare, Send, Sparkles, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage, LessonStartResponse } from "@/types/mission";
import { lessonStartResponseSchema, missionChatResponseSchema } from "@/types/mission";

type MissionTutorChatProps = {
  missionId: string;
};

function chatStorageKey(missionId: string) {
  return `mission:${missionId}:chat`;
}

function lessonStorageKey(missionId: string) {
  return `mission:${missionId}:lesson`;
}

const initialMessages: ChatMessage[] = [
  {
    role: "assistant",
    content: "Review the plan on the right, then ask me if anything is unclear.",
  },
];

export function MissionTutorChat({ missionId }: MissionTutorChatProps) {
  const [messages, setMessages] = React.useState<ChatMessage[]>(initialMessages);
  const [draft, setDraft] = React.useState("");
  const [isSending, setIsSending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [currentLesson, setCurrentLesson] = React.useState<LessonStartResponse | null>(null);

  React.useEffect(() => {
    const cachedChat = window.sessionStorage.getItem(chatStorageKey(missionId));
    if (cachedChat) {
      try {
        setMessages(JSON.parse(cachedChat));
      } catch {
        window.sessionStorage.removeItem(chatStorageKey(missionId));
      }
    }

    const syncLesson = () => {
      const cachedLesson = window.sessionStorage.getItem(lessonStorageKey(missionId));
      if (!cachedLesson) {
        setCurrentLesson(null);
        return;
      }

      try {
        setCurrentLesson(lessonStartResponseSchema.parse(JSON.parse(cachedLesson)));
      } catch {
        window.sessionStorage.removeItem(lessonStorageKey(missionId));
        setCurrentLesson(null);
      }
    };

    syncLesson();
    window.addEventListener("focus", syncLesson);
    return () => window.removeEventListener("focus", syncLesson);
  }, [missionId]);

  React.useEffect(() => {
    window.sessionStorage.setItem(chatStorageKey(missionId), JSON.stringify(messages));
  }, [messages, missionId]);

  async function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || isSending) {
      return;
    }

    const nextMessages = [...messages, { role: "user" as const, content }];
    setMessages(nextMessages);
    setDraft("");
    setIsSending(true);
    setError(null);

    try {
      const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
      const activeLesson = readCachedLesson(missionId) ?? currentLesson;
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: content,
          current_objective_id: activeLesson?.objective_id ?? null,
          history: nextMessages.slice(-6),
        }),
      });

      if (!response.ok) {
        throw new Error(`Tutor chat failed: ${response.status}`);
      }

      const parsed = missionChatResponseSchema.parse(await response.json());
      setMessages((existing) => [...existing, parsed.message]);
    } catch (sendError) {
      console.error("failed to send tutor chat message", sendError);
      setError("The tutor could not respond right now.");
    } finally {
      setIsSending(false);
    }
  }

  return (
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
          type="button"
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 px-5 py-4">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <ChatBubble key={`${message.role}-${index}-${message.content.slice(0, 16)}`} message={message} />
          ))}
          {isSending ? (
            <div className="flex items-start gap-3">
              <Avatar className="mt-0.5 h-7 w-7">
                <AvatarFallback className="bg-indigo-100 text-xs font-medium text-indigo-700">
                  T
                </AvatarFallback>
              </Avatar>
              <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500">
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Tutor is thinking
                </span>
              </div>
            </div>
          ) : null}
          {error ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {error}
            </div>
          ) : null}
        </div>
      </ScrollArea>

      <form className="border-t border-slate-200/80 bg-white px-4 py-3" onSubmit={sendMessage}>
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5">
          <MessageSquare className="h-4 w-4 shrink-0 text-slate-400" />
          <input
            type="text"
            placeholder="Ask about this mission..."
            className="min-w-0 flex-1 border-0 bg-transparent py-1.5 text-sm text-slate-700 outline-none placeholder:text-slate-400"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={isSending}
          />
          <Button
            size="sm"
            className="h-7 rounded-md bg-indigo-600 px-3 text-xs text-white hover:bg-indigo-700"
            type="submit"
            disabled={!draft.trim() || isSending}
          >
            {isSending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="mr-1.5 h-3.5 w-3.5" />}
            send
          </Button>
        </div>
      </form>
    </aside>
  );
}

function readCachedLesson(missionId: string) {
  const cachedLesson = window.sessionStorage.getItem(lessonStorageKey(missionId));
  if (!cachedLesson) {
    return null;
  }

  try {
    return lessonStartResponseSchema.parse(JSON.parse(cachedLesson));
  } catch {
    window.sessionStorage.removeItem(lessonStorageKey(missionId));
    return null;
  }
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className="flex items-start gap-3">
      <Avatar className="mt-0.5 h-7 w-7">
        <AvatarFallback
          className={
            isUser
              ? "bg-slate-200 text-xs font-medium text-slate-600"
              : "bg-indigo-100 text-xs font-medium text-indigo-700"
          }
        >
          {isUser ? <User className="h-3.5 w-3.5" /> : "T"}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700">{isUser ? "You" : "Tutor"}</span>
          <span className="text-xs text-slate-400">now</span>
        </div>
        <div
          className={
            isUser
              ? "rounded-lg border border-indigo-200 bg-indigo-50/60 px-4 py-2.5 text-sm leading-relaxed text-indigo-800"
              : "rounded-lg bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700"
          }
        >
          {message.content}
        </div>
      </div>
    </div>
  );
}
