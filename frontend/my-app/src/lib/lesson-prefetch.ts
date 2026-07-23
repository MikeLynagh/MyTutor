import type { LessonStartResponse, Mission, NextLearningTaskType } from "@/types/mission";
import {
  lessonStartResponseSchema,
  missionSchema,
  nextLearningTaskTypeSchema,
} from "@/types/mission";

export type InitialLessonLoad = {
  missionData: Mission;
  lessonData: LessonStartResponse;
};

const initialLessonLoads = new Map<string, Promise<InitialLessonLoad>>();

export function lessonStorageKey(missionId: string) {
  return `mission:${missionId}:lesson`;
}

export function lessonTaskTypeStorageKey(missionId: string) {
  return `mission:${missionId}:lesson-task-type`;
}

export function missionStorageKey(missionId: string) {
  return `mission:${missionId}`;
}

export function readCachedTaskType(missionId: string): NextLearningTaskType {
  const cachedTaskType = window.sessionStorage.getItem(lessonTaskTypeStorageKey(missionId));
  const parsedTaskType = nextLearningTaskTypeSchema.safeParse(cachedTaskType);
  return parsedTaskType.success ? parsedTaskType.data : "lesson";
}

export function readCachedInitialLesson(missionId: string): InitialLessonLoad | null {
  const cachedMission = window.sessionStorage.getItem(missionStorageKey(missionId));
  const cachedLesson = window.sessionStorage.getItem(lessonStorageKey(missionId));
  const cachedTaskType = window.sessionStorage.getItem(lessonTaskTypeStorageKey(missionId));

  if (!cachedMission || !cachedLesson) {
    return null;
  }

  if (cachedTaskType && cachedTaskType !== "lesson") {
    return null;
  }

  try {
    return {
      missionData: missionSchema.parse(JSON.parse(cachedMission)),
      lessonData: lessonStartResponseSchema.parse(JSON.parse(cachedLesson)),
    };
  } catch {
    window.sessionStorage.removeItem(missionStorageKey(missionId));
    window.sessionStorage.removeItem(lessonStorageKey(missionId));
    window.sessionStorage.removeItem(lessonTaskTypeStorageKey(missionId));
    return null;
  }
}

export function loadInitialLesson(apiUrl: string, missionId: string): Promise<InitialLessonLoad> {
  const cachedLoad = readCachedInitialLesson(missionId);
  if (cachedLoad) {
    return Promise.resolve(cachedLoad);
  }

  const existingLoad = initialLessonLoads.get(missionId);
  if (existingLoad) {
    return existingLoad;
  }

  const load = fetchInitialLesson(apiUrl, missionId)
    .then((lessonLoad) => {
      cacheInitialLesson(missionId, lessonLoad);
      return lessonLoad;
    })
    .finally(() => {
      initialLessonLoads.delete(missionId);
    });

  initialLessonLoads.set(missionId, load);
  return load;
}

export function cacheInitialLesson(missionId: string, lessonLoad: InitialLessonLoad) {
  window.sessionStorage.setItem(missionStorageKey(missionId), JSON.stringify(lessonLoad.missionData));
  window.sessionStorage.setItem(lessonStorageKey(missionId), JSON.stringify(lessonLoad.lessonData));
  window.sessionStorage.setItem(lessonTaskTypeStorageKey(missionId), "lesson");
}

async function fetchInitialLesson(apiUrl: string, missionId: string): Promise<InitialLessonLoad> {
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

  if (!lessonStartResponse.ok) {
    throw new Error(`Failed to start lesson: ${lessonStartResponse.status}`);
  }

  return {
    missionData: missionSchema.parse(await missionResponse.json()),
    lessonData: lessonStartResponseSchema.parse(await lessonStartResponse.json()),
  };
}
