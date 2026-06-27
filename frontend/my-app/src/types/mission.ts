export type CurrentLevel = "beginner" | "some_knowledge" | "comfortable";

export type LearningPreference = "short" | "quiz_often" | "step_by_step";

export type SourceMode = "web" | "user_material" | "both";

export type MissionType =
  | "procedural_skill"
  | "technical_skill"
  | "conceptual_topic"
  | "interview_prep";

export type ResourceType =
  | "article"
  | "video"
  | "documentation"
  | "guide"
  | "user_material"
  | "other";

export type AssessmentType =
  | "short_written_answer"
  | "multiple_choice"
  | "practical_check"
  | "free_form";

export type NextActionType =
  | "remediate"
  | "repeat_with_new_example"
  | "practical_check"
  | "advance";

export type MissionCreate = {
  goal: string;
  why: string;
  success_criteria: string;
  current_level: CurrentLevel;
  learning_preference: LearningPreference;
  source_mode: SourceMode;
};

export type Mission = {
  id: string;
  title: string;
  goal: string;
  why: string;
  success_criteria: string;
  current_level: CurrentLevel;
  learning_preference: LearningPreference;
  source_mode: SourceMode;
  mission_type: MissionType;
};

export type MissionPlanRequest = {
  goal: string;
  source_mode: SourceMode;
  user_material?: string;
};

export type MissionPlanResponse = {
  mission_id: string;
  selected_sources: CuratedResource[];
  rejected_sources: RejectedResource[];
  source_summary: string;
  recommended_learning_approach: string;
  mission_type: MissionType;
  objectives: Objective[];
  diagnostic_questions: string[];
};

export type Objective = {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  assessment_type: AssessmentType;
  prerequisites: string[];
  success_criteria: string;
};

export type CuratedResource = {
  title: string;
  url: string;
  type: ResourceType;
  reason: string;
};

export type RejectedResource = {
  title: string;
  url: string;
  reason: string;
};

export type CuratedResourceBundle = {
  selected_sources: CuratedResource[];
  rejected_sources: RejectedResource[];
  source_summary: string;
  recommended_learning_approach: string;
};

export type LearningPlan = {
  mission_type: MissionType;
  objectives: Objective[];
  diagnostic_questions: string[];
};

export type Assessment = {
  type: AssessmentType;
  question: string;
  expected_answer?: string | null;
  rubric: string[];
  options: string[];
};

export type PracticalTask = {
  instruction: string;
  success_criteria: string;
};

export type LessonArtifact = {
  lesson_id: string;
  objective_id: string;
  title: string;
  estimated_minutes: number;
  lesson_html: string;
  key_points: string[];
  practical_task?: PracticalTask | null;
  assessment: Assessment;
};

export type EvaluationResult = {
  is_correct: boolean;
  score: number;
  feedback: string;
  misconception?: string | null;
  missing_points: string[];
  next_hint?: string | null;
};

export type MasteryState = {
  objective_id: string;
  p_mastery: number;
  attempts: number;
  recent_errors: string[];
  last_feedback?: string | null;
};

export type MasteryUpdate = {
  objective_id: string;
  mastery_before: number;
  mastery_after: number;
};

export type NextAction = {
  type: NextActionType;
  reason: string;
};
