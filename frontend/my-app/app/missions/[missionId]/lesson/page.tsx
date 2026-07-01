"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { LessonStartResponse, Mission } from "@/types/mission";
import { lessonStartResponseSchema, missionSchema } from "@/types/mission";

function lessonStorageKey(missionId: string) {
  return `mission:${missionId}:lesson`;
}

function missionStorageKey(missionId: string) {
  return `mission:${missionId}`;
}

export default function MissionLessonPage() {
  const params = useParams<{ missionId: string }>();
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [lessonResponse, setLessonResponse] = React.useState<LessonStartResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isRegenerating, setIsRegenerating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [answer, setAnswer] = React.useState("");

  React.useEffect(() => {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    const cachedMission = window.sessionStorage.getItem(missionStorageKey(missionId));
    if (cachedMission) {
      try {
        setMission(missionSchema.parse(JSON.parse(cachedMission)));
      } catch {
        window.sessionStorage.removeItem(missionStorageKey(missionId));
      }
    }

    const cachedLesson = window.sessionStorage.getItem(lessonStorageKey(missionId));
    if (cachedLesson) {
      try {
        setLessonResponse(lessonStartResponseSchema.parse(JSON.parse(cachedLesson)));
      } catch {
        window.sessionStorage.removeItem(lessonStorageKey(missionId));
      }
    }

    async function loadLesson() {
      try {
        const [missionResponse, lessonStartResponse] = await Promise.all([
          fetch(`${apiUrl}/api/missions/${missionId}`),
          fetch(`${apiUrl}/api/missions/${missionId}/lessons/start`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          }),
        ]);

        if (!missionResponse.ok) {
          throw new Error(`Failed to load mission: ${missionResponse.status}`);
        }

        const missionData = missionSchema.parse(await missionResponse.json());
        setMission(missionData);
        window.sessionStorage.setItem(missionStorageKey(missionId), JSON.stringify(missionData));

        if (!lessonStartResponse.ok) {
          throw new Error(`Failed to start lesson: ${lessonStartResponse.status}`);
        }

        const lessonData = lessonStartResponseSchema.parse(await lessonStartResponse.json());
        setLessonResponse(lessonData);
        window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
        setError(null);
      } catch (loadError) {
        console.error("failed to load lesson", loadError);
        if (!cachedLesson) {
          setError("Could not load the first lesson for this mission.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    void loadLesson();
  }, [params.missionId]);

  async function regenerateLesson() {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    setIsRegenerating(true);
    try {
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/lessons/start?force=true`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to regenerate lesson: ${response.status}`);
      }

      const lessonData = lessonStartResponseSchema.parse(await response.json());
      setLessonResponse(lessonData);
      setAnswer("");
      window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
      setError(null);
    } catch (regenerateError) {
      console.error("failed to regenerate lesson", regenerateError);
      setError("Could not regenerate the lesson.");
    } finally {
      setIsRegenerating(false);
    }
  }

  if (isLoading && !lessonResponse) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="size-4 animate-spin" />
          Starting lesson
        </div>
      </div>
    );
  }

  if (error && !lessonResponse) {
    return (
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-800">Lesson unavailable</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{error}</p>
        <Button asChild variant="outline" className="mt-6 border-slate-200 text-slate-600 hover:bg-slate-50">
          <Link href={`/missions/${params.missionId}/plan`}>Back to plan</Link>
        </Button>
      </div>
    );
  }

  if (!lessonResponse) {
    return null;
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
          <span>Lesson 1</span>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 gap-1 border-slate-200 text-xs text-slate-600 hover:bg-slate-50"
          onClick={regenerateLesson}
          disabled={isRegenerating}
        >
          <RefreshCcw className={isRegenerating ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
          Regenerate
        </Button>
      </div>
      <h1 className="mb-4 text-2xl font-bold leading-tight text-slate-800">
        {lessonResponse.lesson.title}
      </h1>
      <p className="mb-6 text-sm italic leading-relaxed text-slate-600">
        Your mission: {mission?.goal ?? "build this skill step by step"}. This lesson covers{" "}
        {lessonResponse.objective_id} and prepares you for the assessment below.
      </p>

      <article
        className="text-sm leading-relaxed text-slate-600 [&_blockquote]:mt-4 [&_blockquote]:border-l-2 [&_blockquote]:border-indigo-200 [&_blockquote]:pl-4 [&_blockquote]:text-slate-500 [&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-xs [&_h2]:mb-2 [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-slate-800 [&_h3]:mb-2 [&_h3]:mt-5 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-slate-800 [&_li]:pl-1 [&_ol]:mt-2 [&_ol]:list-decimal [&_ol]:space-y-1 [&_ol]:pl-5 [&_p]:mt-3 [&_pre]:mt-3 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-slate-950 [&_pre]:p-4 [&_pre]:text-xs [&_pre]:text-slate-100 [&_strong]:font-semibold [&_strong]:text-slate-800 [&_ul]:mt-2 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-5"
        dangerouslySetInnerHTML={{ __html: lessonResponse.lesson.lesson_html }}
      />

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-semibold text-slate-800">Key points</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed text-slate-600">
          {lessonResponse.lesson.key_points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      {lessonResponse.lesson.practical_task ? (
        <section className="mt-8">
          <h2 className="mb-2 text-lg font-semibold text-slate-800">Practical task</h2>
          <p className="text-sm leading-relaxed text-slate-600">
            {lessonResponse.lesson.practical_task.instruction}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            <strong className="font-semibold text-slate-800">Success criteria:</strong>{" "}
            {lessonResponse.lesson.practical_task.success_criteria}
          </p>
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-semibold text-slate-800">Assessment</h2>
        <p className="text-sm leading-relaxed text-slate-600">
          {lessonResponse.lesson.assessment.question}
        </p>
        {lessonResponse.lesson.assessment.rubric.length > 0 ? (
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
            {lessonResponse.lesson.assessment.rubric.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        ) : null}
      </section>

      <form
        className="mt-6"
        onSubmit={(event) => {
          event.preventDefault();
        }}
      >
        <Textarea
          className="min-h-28 resize-none rounded-lg border-slate-200 text-sm text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-400"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Write your answer here"
        />
        <div className="mt-3 flex justify-end">
          <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700" disabled={!answer.trim()}>
            Submit Answer
          </Button>
        </div>
      </form>

      <div className="mt-8 flex items-center justify-between border-t border-slate-200/60 pt-4">
        <Button variant="outline" size="sm" className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50" disabled>
          <ChevronLeft className="h-4 w-4" />
          Previous Lesson
        </Button>
        <span className="text-xs text-slate-400">Lesson 1</span>
        <Button asChild size="sm" className="gap-1 bg-indigo-600 hover:bg-indigo-700">
          <Link href={`/missions/${params.missionId}/progress`}>
            Ready for next lesson
            <ChevronRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
