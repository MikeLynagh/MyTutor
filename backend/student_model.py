class StudentModel:
    """Maintains per-student mastery state across all learning objectives. Updated after every session"""

    def __init__(self, student_id: str, knowledge_graph):
        self.student_id = student_id
        self.knowledge_graph = knowledge_graph
        self.mastery = {
            obj.id: {
                "p_master": 0.1,
                "attempts": 0,
                "last_seen": None,
                "recent_errors": [],
            } 
            for obj in knowledge_graph.objectives
        }

    def get_mastery_state(self) -> dict: 
        """Return current mastery probabilities"""
        return {
            oid: state["p_mastery"]
            for oid, state in self.mastery.items()
        }
    
    def get_recent_errors(self, objective_id: str):
        return self.mastery[objective_id].get('recent_errors', [])
    
    def get_mastered_objectives(self, threshold=0.85):
        return [
            oid for oid, state
            in self.mastery.items()
            if state["p_mastery"] >= threshold
        ]
    
    def update_mastery(self, objective_id: str,
                       new_p: float, error=None):
        state = self.mastery[objective_id]
        state["p_mastery"] = new_p
        state["attempts"] += 1
        if error is not None:
            state["recent_errors"].append(error)
            state["recent_errors"] = (
                state["recent_errors"][-5:])