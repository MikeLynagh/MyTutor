from app.models.learner import MissionLearnerState, ObjectiveMasteryState
from app.schemas.mission import Mission
from app.schemas.lesson import LessonArtifact
from app.schemas.mission_plan import MissionPlanResponse


class MemoryStore:
    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}
        self._mission_plans: dict[str, MissionPlanResponse] = {}
        self._lessons: dict[tuple[str, str], LessonArtifact] = {}
        self._learner_states: dict[str, MissionLearnerState] = {}

    def save_mission(self, mission: Mission) -> Mission:
        self._missions[mission.id] = mission
        return mission

    def get_mission(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def save_mission_plan(self, mission_id: str, mission_plan: MissionPlanResponse) -> MissionPlanResponse:
        self._mission_plans[mission_id] = mission_plan
        return mission_plan

    def get_mission_plan(self, mission_id: str) -> MissionPlanResponse | None:
        return self._mission_plans.get(mission_id)

    def save_lesson(self, mission_id: str, lesson: LessonArtifact) -> LessonArtifact:
        self._lessons[(mission_id, lesson.objective_id)] = lesson
        return lesson

    def get_lesson(self, mission_id: str, objective_id: str) -> LessonArtifact | None:
        return self._lessons.get((mission_id, objective_id))

    def get_learner_state(self, mission_id: str) -> MissionLearnerState:
        learner_state = self._learner_states.get(mission_id)
        if learner_state is None:
            learner_state = MissionLearnerState(mission_id=mission_id)
            self._learner_states[mission_id] = learner_state
        return learner_state

    def get_objective_mastery(self, mission_id: str, objective_id: str) -> ObjectiveMasteryState:
        learner_state = self.get_learner_state(mission_id)
        objective_state = learner_state.objectives.get(objective_id)
        if objective_state is None:
            objective_state = ObjectiveMasteryState(objective_id=objective_id)
            learner_state.objectives[objective_id] = objective_state
        return objective_state

    def save_objective_mastery(
        self,
        mission_id: str,
        objective_state: ObjectiveMasteryState,
    ) -> ObjectiveMasteryState:
        learner_state = self.get_learner_state(mission_id)
        learner_state.objectives[objective_state.objective_id] = objective_state
        return objective_state


memory_store = MemoryStore()
