import { z } from "zod";

export const currentLevelSchema = z.enum(["beginner", "some_knowledge", "comfortable"]);

export const learningPreferenceSchema = z.enum(["short", "quiz_often", "step_by_step"]);

export const sourceModeSchema = z.enum(["web", "user_material", "both"]);

export const missionTypeSchema = z.enum([
  "procedural_skill",
  "technical_skill",
  "conceptual_topic",
  "interview_prep",
]);

export const resourceTypeSchema = z.enum([
  "article",
  "video",
  "documentation",
  "guide",
  "user_material",
  "other",
]);

export const assessmentTypeSchema = z.enum([
  "short_written_answer",
  "multiple_choice",
  "practical_check",
  "free_form",
]);

export const nextActionTypeSchema = z.enum([
  "remediate",
  "repeat_with_new_example",
  "practical_check",
  "advance",
]);

export const missionCreateSchema = z.object({
  goal: z.string(),
  why: z.string(),
  success_criteria: z.string(),
  current_level: currentLevelSchema,
  learning_preference: learningPreferenceSchema,
  source_mode: sourceModeSchema,
});

export const missionSchema = missionCreateSchema.extend({
  id: z.string(),
  title: z.string(),
  mission_type: missionTypeSchema,
});

export const missionPlanRequestSchema = z.object({
  goal: z.string(),
  source_mode: sourceModeSchema,
  user_material: z.string().optional(),
});

export const objectiveSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  difficulty: z.number().min(0).max(1),
  assessment_type: assessmentTypeSchema,
  prerequisites: z.array(z.string()),
  success_criteria: z.string(),
});

export const curatedResourceSchema = z.object({
  title: z.string(),
  url: z.string(),
  type: resourceTypeSchema,
  reason: z.string(),
});

export const rejectedResourceSchema = z.object({
  title: z.string(),
  url: z.string(),
  reason: z.string(),
});

export const curatedResourceBundleSchema = z.object({
  selected_sources: z.array(curatedResourceSchema),
  rejected_sources: z.array(rejectedResourceSchema),
  source_summary: z.string(),
  recommended_learning_approach: z.string(),
});

export const learningPlanSchema = z.object({
  mission_type: missionTypeSchema,
  objectives: z.array(objectiveSchema),
  diagnostic_questions: z.array(z.string()),
});

export const missionPlanResponseSchema = curatedResourceBundleSchema
  .merge(learningPlanSchema)
  .extend({
    mission_id: z.string(),
  });

export const assessmentSchema = z.object({
  type: assessmentTypeSchema,
  question: z.string(),
  expected_answer: z.string().nullable().optional(),
  rubric: z.array(z.string()),
  options: z.array(z.string()),
});

export const practicalTaskSchema = z.object({
  instruction: z.string(),
  success_criteria: z.string(),
});

export const lessonArtifactSchema = z.object({
  lesson_id: z.string(),
  objective_id: z.string(),
  title: z.string(),
  lesson_html: z.string(),
  key_points: z.array(z.string()),
  practical_task: practicalTaskSchema,
  assessment: assessmentSchema,
});

export const lessonStartResponseSchema = z.object({
  mission_id: z.string(),
  objective_id: z.string(),
  lesson: lessonArtifactSchema,
});

export const answerSubmissionSchema = z.object({
  lesson_id: z.string(),
  objective_id: z.string(),
  answer: z.string().trim().min(1),
});

export const answerSubmissionResponseSchema = answerSubmissionSchema.extend({
  status: z.literal("received"),
  message: z.string(),
});

export const evaluationResultSchema = z.object({
  is_correct: z.boolean(),
  score: z.number().min(0).max(1),
  feedback: z.string(),
  misconception: z.string().nullable().optional(),
  missing_points: z.array(z.string()),
  next_hint: z.string().nullable().optional(),
});

export const masteryStateSchema = z.object({
  objective_id: z.string(),
  p_mastery: z.number().min(0).max(1),
  attempts: z.number().int().min(0),
  recent_errors: z.array(z.string()),
  last_feedback: z.string().nullable().optional(),
});

export const masteryUpdateSchema = z.object({
  objective_id: z.string(),
  mastery_before: z.number().min(0).max(1),
  mastery_after: z.number().min(0).max(1),
});

export const nextActionSchema = z.object({
  type: nextActionTypeSchema,
  reason: z.string(),
});

export const answerEvaluationResponseSchema = z.object({
  evaluation: evaluationResultSchema,
  mastery: masteryUpdateSchema,
  next_action: nextActionSchema,
});

export const answerEvaluationWithMasteryResponseSchema = z.object({
  evaluation: evaluationResultSchema,
  mastery: masteryUpdateSchema,
});

export type CurrentLevel = z.infer<typeof currentLevelSchema>;
export type LearningPreference = z.infer<typeof learningPreferenceSchema>;
export type SourceMode = z.infer<typeof sourceModeSchema>;
export type MissionType = z.infer<typeof missionTypeSchema>;
export type ResourceType = z.infer<typeof resourceTypeSchema>;
export type AssessmentType = z.infer<typeof assessmentTypeSchema>;
export type NextActionType = z.infer<typeof nextActionTypeSchema>;
export type MissionCreate = z.infer<typeof missionCreateSchema>;
export type Mission = z.infer<typeof missionSchema>;
export type MissionPlanRequest = z.infer<typeof missionPlanRequestSchema>;
export type MissionPlanResponse = z.infer<typeof missionPlanResponseSchema>;
export type Objective = z.infer<typeof objectiveSchema>;
export type CuratedResource = z.infer<typeof curatedResourceSchema>;
export type RejectedResource = z.infer<typeof rejectedResourceSchema>;
export type CuratedResourceBundle = z.infer<typeof curatedResourceBundleSchema>;
export type LearningPlan = z.infer<typeof learningPlanSchema>;
export type Assessment = z.infer<typeof assessmentSchema>;
export type PracticalTask = z.infer<typeof practicalTaskSchema>;
export type LessonArtifact = z.infer<typeof lessonArtifactSchema>;
export type LessonStartResponse = z.infer<typeof lessonStartResponseSchema>;
export type AnswerSubmission = z.infer<typeof answerSubmissionSchema>;
export type AnswerSubmissionResponse = z.infer<typeof answerSubmissionResponseSchema>;
export type EvaluationResult = z.infer<typeof evaluationResultSchema>;
export type MasteryState = z.infer<typeof masteryStateSchema>;
export type MasteryUpdate = z.infer<typeof masteryUpdateSchema>;
export type NextAction = z.infer<typeof nextActionSchema>;
export type AnswerEvaluationResponse = z.infer<typeof answerEvaluationResponseSchema>;
export type answerEvaluationWithMasteryResponse = z.infer<typeof answerEvaluationWithMasteryResponseSchema>;
