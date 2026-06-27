from app.schemas.mission import Mission


class MemoryStore:
    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}

    def save_mission(self, mission: Mission) -> Mission:
        self._missions[mission.id] = mission
        return mission

    def get_mission(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)


memory_store = MemoryStore()
