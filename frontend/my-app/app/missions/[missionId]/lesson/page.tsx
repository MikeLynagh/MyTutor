"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import type { answerEvaluationWithMasteryResponse, LessonStartResponse, Mission, PracticeTask } from "@/types/mission";
import {
  answerEvaluationWithMasteryResponseSchema,
  lessonStartResponseSchema,
  missionSchema,
  nextTaskResponseSchema,
} from "@/types/mission";

function lessonStorageKey(missionId: string) {
  return `mission:${missionId}:lesson`;
}

function missionStorageKey(missionId: string) {
  return `mission:${missionId}`;
}

function formatAssessmentType(type: string) {
  return type.replaceAll("_", " ");
}

function formatPracticePurpose(purpose: string) {
  return purpose.replaceAll("_", " ");
}

function checklistItemsFromSuccessCriteria(successCriteria: string) {
  const items = successCriteria
    .split(/[.;]\s+/)
    .map((item) => item.trim().replace(/[.;]$/, ""))
    .filter(Boolean)
    .slice(0, 8);

  return items.length > 0 ? items : ["I completed the practical task."];
}

function fieldId(prefix: string, value: string, index: number) {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);

  return `${prefix}-${index}-${slug || "item"}`;
}

export default function MissionLessonPage() {
  const params = useParams<{ missionId: string }>();
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [lessonResponse, setLessonResponse] = React.useState<LessonStartResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isRegenerating, setIsRegenerating] = React.useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = React.useState(false);
  const [isContinuing, setIsContinuing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [answer, setAnswer] = React.useState("");
  const [selectedOption, setSelectedOption] = React.useState("");
  const [completedChecks, setCompletedChecks] = React.useState<string[]>([]);
  const [practicalReflection, setPracticalReflection] = React.useState("");
  const [answerEvaluation, setAnswerEvaluation] = React.useState<answerEvaluationWithMasteryResponse | null>(null);

  const assessment = lessonResponse?.lesson.assessment;
  const practicalChecklistItems = React.useMemo(
    () =>
      checklistItemsFromSuccessCriteria(
        lessonResponse?.lesson.practical_task?.success_criteria ||
          lessonResponse?.lesson.assessment.expected_answer ||
          "",
      ),
    [lessonResponse?.lesson.practical_task?.success_criteria, lessonResponse?.lesson.assessment.expected_answer],
  );
  const canSubmitAnswer = React.useMemo(() => {
    if (!assessment) {
      return false;
    }

    if (assessment.type === "multiple_choice") {
      if (assessment.options.length === 0) {
        return answer.trim().length > 0;
      }

      return selectedOption.trim().length > 0;
    }

    if (assessment.type === "practical_check") {
      return practicalChecklistItems.every((item) => completedChecks.includes(item));
    }

    return answer.trim().length > 0;
  }, [answer, assessment, completedChecks, practicalChecklistItems, selectedOption]);

  React.useEffect(() => {
    setAnswer("");
    setSelectedOption("");
    setCompletedChecks([]);
    setPracticalReflection("");
    setAnswerEvaluation(null);
  }, [lessonResponse?.lesson.lesson_id]);

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
    setError(null);
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
      window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
      setError(null);
    } catch (regenerateError) {
      console.error("failed to regenerate lesson", regenerateError);
      setError("Could not regenerate the lesson.");
    } finally {
      setIsRegenerating(false);
    }
  }

  async function submitAnswer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!lessonResponse || !canSubmitAnswer) {
      return;
    }

    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    setIsSubmittingAnswer(true);
    setAnswerEvaluation(null);
    setError(null);
    try {
      const submittedAnswer = buildSubmittedAnswer({
        assessmentType: lessonResponse.lesson.assessment.type,
        writtenAnswer: answer,
        selectedOption,
        completedChecks,
        practicalReflection,
      });
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/answers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lesson_id: lessonResponse.lesson.lesson_id,
          objective_id: lessonResponse.lesson.objective_id,
          answer: submittedAnswer,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit answer: ${response.status}`);
      }

      const evaluation = answerEvaluationWithMasteryResponseSchema.parse(await response.json());
      setAnswerEvaluation(evaluation);
      setError(null);
    } catch (submitError) {
      console.error("failed to submit answer", submitError);
      setError("Could not submit your answer.");
    } finally {
      setIsSubmittingAnswer(false);
    }
  }

  async function continueToNextTask() {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const missionId = params.missionId;

    setIsContinuing(true);
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/api/missions/${missionId}/tasks/next`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load next task: ${response.status}`);
      }

      const nextTaskResponse = nextTaskResponseSchema.parse(await response.json());
      const lessonData: LessonStartResponse = {
        mission_id: nextTaskResponse.mission_id,
        objective_id: nextTaskResponse.objective_id,
        lesson: nextTaskResponse.lesson,
      };

      setLessonResponse(lessonData);
      window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonData));
      setError(null);
    } catch (continueError) {
      console.error("failed to continue to next task", continueError);
      setError("Could not load the next task.");
    } finally {
      setIsContinuing(false);
    }
  }

  if (isLoading && !lessonResponse) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="max-w-sm rounded-lg border border-slate-200 bg-slate-50 px-5 py-4 text-center">
          <Loader2 className="mx-auto h-5 w-5 animate-spin text-indigo-600" />
          <p className="mt-3 text-sm font-medium text-slate-800">Generating your lesson</p>
          <p className="mt-1 text-sm leading-relaxed text-slate-500">
            The tutor is turning your first objective into a guided lesson and assessment.
          </p>
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
      {isRegenerating || isContinuing ? (
        <div className="mb-5 rounded-lg border border-indigo-200 bg-indigo-50/70 px-4 py-3">
          <div className="flex items-start gap-3">
            <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-indigo-600" />
            <div>
              <p className="text-sm font-medium text-indigo-950">
                {isContinuing ? "Preparing your next task" : "Regenerating this lesson"}
              </p>
              <p className="mt-1 text-sm leading-relaxed text-indigo-900/80">
                {isContinuing
                  ? "The tutor is using your latest answer and mastery estimate to decide what to show next."
                  : "The tutor is creating a fresh version of this lesson from the current objective."}
              </p>
            </div>
          </div>
        </div>
      ) : null}
      {error ? (
        <div className="mb-5 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      ) : null}
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
          disabled={isRegenerating || isContinuing || isSubmittingAnswer}
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
        className="lesson-html"
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

      {lessonResponse.lesson.practice_tasks.length > 0 ? (
        <PracticeTasks tasks={lessonResponse.lesson.practice_tasks} />
      ) : null}

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
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-indigo-600">
          {formatAssessmentType(lessonResponse.lesson.assessment.type)}
        </p>
        <p className="text-sm leading-relaxed text-slate-600">
          {lessonResponse.lesson.assessment.question}
        </p>
      </section>

      <form
        className="mt-6"
        onSubmit={submitAnswer}
      >
        {lessonResponse.lesson.assessment.type === "multiple_choice" ? (
          <MultipleChoiceAnswer
            options={lessonResponse.lesson.assessment.options}
            selectedOption={selectedOption}
            onChange={setSelectedOption}
            fallbackAnswer={answer}
            onFallbackAnswerChange={setAnswer}
            disabled={isSubmittingAnswer || isContinuing || isRegenerating}
          />
        ) : lessonResponse.lesson.assessment.type === "practical_check" ? (
          <PracticalCheckAnswer
            checklistItems={practicalChecklistItems}
            completedChecks={completedChecks}
            onCompletedChecksChange={setCompletedChecks}
            reflection={practicalReflection}
            onReflectionChange={setPracticalReflection}
            disabled={isSubmittingAnswer || isContinuing || isRegenerating}
          />
        ) : (
          <Textarea
            className="min-h-28 resize-none rounded-lg border-slate-200 text-sm text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-400"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Write your answer here"
            disabled={isSubmittingAnswer || isContinuing || isRegenerating}
          />
        )}
        <div className="mt-3 flex justify-end">
          <Button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={!canSubmitAnswer || isSubmittingAnswer || isContinuing || isRegenerating}
          >
            {isSubmittingAnswer ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Checking answer
              </>
            ) : (
              "Submit Answer"
            )}
          </Button>
        </div>
      </form>

      {answerEvaluation ? (
        <section className="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-900">Feedback</h2>
            <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600">
              Score {Math.round(answerEvaluation.evaluation.score * 100)}%
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-700">
            {answerEvaluation.evaluation.feedback}
          </p>
          {answerEvaluation.evaluation.misconception ? (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <span className="font-medium text-slate-800">Possible misconception:</span>{" "}
              {answerEvaluation.evaluation.misconception}
            </p>
          ) : null}
          {answerEvaluation.evaluation.missing_points.length > 0 ? (
            <div className="mt-3">
              <p className="text-sm font-medium text-slate-800">Missing points</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
                {answerEvaluation.evaluation.missing_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {answerEvaluation.evaluation.next_hint ? (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <span className="font-medium text-slate-800">Hint:</span>{" "}
              {answerEvaluation.evaluation.next_hint}
            </p>
          ) : null}
          <p className="mt-3 text-sm leading-relaxed text-slate-800">
            <span className="font-medium text-slate-800">Mastery:</span>{' '}
            {Math.round(answerEvaluation.mastery.mastery_before * 100)}% → {Math.round(
              answerEvaluation.mastery.mastery_after * 100,
            )}%
          </p>
          <div className="mt-4 border-t border-slate-200 pt-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-indigo-600">Next task</p>
                <h3 className="mt-1 text-base font-semibold text-slate-900">
                  {answerEvaluation.next_task.title}
                </h3>
              </div>
              <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-500">
                {answerEvaluation.next_task.type.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-slate-700">
              {answerEvaluation.next_task.reason}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              {answerEvaluation.next_task.instruction}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <span className="font-medium text-slate-800">Success criteria:</span>{" "}
              {answerEvaluation.next_task.success_criteria}
            </p>
            <div className="mt-4 flex justify-end">
              <Button
                type="button"
                className="gap-1 bg-indigo-600 hover:bg-indigo-700"
                onClick={continueToNextTask}
                disabled={isContinuing}
              >
                {isContinuing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading next task
                  </>
                ) : (
                  <>
                    Continue
                    <ChevronRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </section>
      ) : null}

      <div className="mt-8 flex items-center justify-between border-t border-slate-200/60 pt-4">
        <Button variant="outline" size="sm" className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50" disabled>
          <ChevronLeft className="h-4 w-4" />
          Previous Lesson
        </Button>
        <span className="text-xs text-slate-400">Lesson 1</span>
        <Button asChild variant="outline" size="sm" className="gap-1 border-slate-200 text-slate-600 hover:bg-slate-50">
          <Link href={`/missions/${params.missionId}/progress`}>Progress</Link>
        </Button>
      </div>
    </div>
  );
}

function PracticeTasks({ tasks }: { tasks: PracticeTask[] }) {
  return (
    <section className="mt-8">
      <h2 className="mb-2 text-lg font-semibold text-slate-800">Practice rounds</h2>
      <ol className="space-y-3">
        {tasks.map((task, index) => (
          <li key={task.id || `${task.prompt}-${index}`} className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wider text-indigo-600">
              Round {index + 1} · {formatPracticePurpose(task.purpose)}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{task.prompt}</p>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              <strong className="font-semibold text-slate-800">Success criteria:</strong>{" "}
              {task.success_criteria}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function MultipleChoiceAnswer({
  options,
  selectedOption,
  onChange,
  fallbackAnswer,
  onFallbackAnswerChange,
  disabled,
}: {
  options: string[];
  selectedOption: string;
  onChange: (value: string) => void;
  fallbackAnswer: string;
  onFallbackAnswerChange: (value: string) => void;
  disabled: boolean;
}) {
  if (options.length === 0) {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          This question is marked as multiple choice, but no answer options were generated. Answer in your own words.
        </div>
        <Textarea
          className="min-h-24 resize-none rounded-lg border-slate-200 text-sm text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-400"
          value={fallbackAnswer}
          onChange={(event) => onFallbackAnswerChange(event.target.value)}
          placeholder="Write your answer here"
          disabled={disabled}
        />
      </div>
    );
  }

  return (
    <RadioGroup value={selectedOption} onValueChange={onChange} disabled={disabled} className="gap-2">
      {options.map((option, index) => {
        const id = fieldId("assessment-option", option, index);

        return (
          <label
            key={option}
            htmlFor={id}
            className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 px-4 py-3 text-sm text-slate-700 transition-colors hover:bg-slate-50 has-[[data-state=checked]]:border-indigo-300 has-[[data-state=checked]]:bg-indigo-50/70"
          >
            <RadioGroupItem id={id} value={option} className="mt-0.5" />
            <span>{option}</span>
          </label>
        );
      })}
    </RadioGroup>
  );
}

function PracticalCheckAnswer({
  checklistItems,
  completedChecks,
  onCompletedChecksChange,
  reflection,
  onReflectionChange,
  disabled,
}: {
  checklistItems: string[];
  completedChecks: string[];
  onCompletedChecksChange: (value: string[]) => void;
  reflection: string;
  onReflectionChange: (value: string) => void;
  disabled: boolean;
}) {
  function toggleCheck(item: string) {
    if (completedChecks.includes(item)) {
      onCompletedChecksChange(completedChecks.filter((check) => check !== item));
      return;
    }

    onCompletedChecksChange([...completedChecks, item]);
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
        <p className="text-sm font-medium text-slate-800">Confirm what you completed</p>
        <div className="mt-3 space-y-2">
          {checklistItems.map((item, index) => {
            const id = fieldId("practical-check", item, index);
            const checked = completedChecks.includes(item);

            return (
              <label key={item} htmlFor={id} className="flex items-start gap-3 text-sm text-slate-700">
                <input
                  id={id}
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => toggleCheck(item)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>{item}</span>
              </label>
            );
          })}
        </div>
      </div>
      <Textarea
        className="min-h-24 resize-none rounded-lg border-slate-200 text-sm text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-400"
        value={reflection}
        onChange={(event) => onReflectionChange(event.target.value)}
        placeholder="Optional: add what you noticed while doing the practical task"
        disabled={disabled}
      />
    </div>
  );
}

function buildSubmittedAnswer({
  assessmentType,
  writtenAnswer,
  selectedOption,
  completedChecks,
  practicalReflection,
}: {
  assessmentType: string;
  writtenAnswer: string;
  selectedOption: string;
  completedChecks: string[];
  practicalReflection: string;
}) {
  if (assessmentType === "multiple_choice") {
    return selectedOption.trim()
      ? `Selected option: ${selectedOption}`
      : writtenAnswer.trim();
  }

  if (assessmentType === "practical_check") {
    const completed = completedChecks.map((check) => `- ${check}`).join("\n");
    const reflection = practicalReflection.trim()
      ? `\nReflection: ${practicalReflection.trim()}`
      : "";

    return `Practical task completed.\nChecklist:\n${completed}${reflection}`;
  }

  return writtenAnswer.trim();
}
