class CurriculumPlanner:
    def __init__(self, knowledge_graph, student_model, content_library):
        self.graph = knowledge_graph
        self.model = student_model
        self.content = content_library
        self.mastery_threshold = 0.8
        
    def get_next_objectives(self, student_id: str, n:int = 3) -> list[LearningObjective]:
        """Select the next learning objectives based on student mastery state and prerequisite constraints"""
        mastery = self.model.get_mastery_state(student_id)
        eligible = []
        for objective in self.graph.get_all_objectives():
            prereqs = self.graph.get_prerequisites(objective.id)
            prereqs_met = all(
                mastery.get(p.id, 0.0) >= self.mastery_threshold
                for p in prereqs
            )
            not_mastered = (
                mastery.get(objective.id, 0.0)
                < self.mastery_threshold
            )
            if prereqs_met and not_mastered:
                eligible.append(objective)
        ranked = sorted(
            eligible, 
            key = lambda obj: self._expected_gain(
                obj, mastery, student_id
            ), 
            reverse=True
        )
        return ranked[:n]
    


    # delta  = 0.2 sets the optimal gap between current mastery and task difficultyu at 
    # 20 percent above the learners level (zone of proximal development)
    # sigma = 0.25 contrls the width of the effective learning zone, determining how sharply the gain function
    # drops off for tasks that are too easy or too hard c
    def _expected_gain(self, objective, mastery, student_id) -> flat:
        """Estimate learning gain using ZPD aligned gaussian model"""
        current = mastery.get(objective.id, 0,0)
        difficulty = objective.estimated_difficulty
        delta = 0.2
        sigma = 0.25
        zpd_score = math.exp(
            -((difficulty - current - delta) ** 2)
            / (2 * sigma ** 2)
        )
        downstream = len(
            self.graph.get_dependants(objective.id)
        )
        return zpd_score * (1 + 0.1 * downstream)