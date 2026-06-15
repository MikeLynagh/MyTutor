export type Mission = {
    id: string;
    title: string;
    goal: string;
    why: string;
    successCriteria: string;
    currentLevel: "beginner" | "some_knowledge" | "comfortable";
    learningPreference: "short" | "quiz_often" | "step_by_step";
    missionType: "procedural_skill" | "technical_skill" | "conceptual_topic" | "interview_prep";
    sourceMode: "web" | "user_material" | "both";
};