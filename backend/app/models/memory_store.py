from app.schemas.mission import Mission
from app.schemas.lesson import LessonArtifact
from app.schemas.mission_plan import MissionPlanResponse


class MemoryStore:
    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}
        self._mission_plans: dict[str, MissionPlanResponse] = {}
        self._lessons: dict[tuple[str, str], LessonArtifact] = {}

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


memory_store = MemoryStore()
