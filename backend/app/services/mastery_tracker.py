from app.schemas.mastery import MasteryUpdate


# this is thresholded Bayesian Knowledge Tracing, the evaluator gives a score from 0 to 1
# The mastery tracker converts that into binary evidence
class MasteryTracker:
    def __init__(self, *, p_learn: float = 0.2, p_guess: float = 0.2, p_slip: float = 0.1, correct_threshold: float = 0.75,
                 ) -> None:
        self.p_learn = p_learn
        self.p_guess = p_guess
        self.p_slip = p_slip
        self.correct_threshold = correct_threshold


    def update(self, *, objective_id: str, current_mastery: float, score: float,
               ) -> MasteryUpdate:
        is_correct = score >= self.correct_threshold
        mastery_before = self._clamp(current_mastery)
        posterior = self._posterior_after_observation(
            p_mastery=mastery_before,
            is_correct=is_correct
        )
        mastery_after = posterior + (1 - posterior) * self.p_learn

        return MasteryUpdate(
            objective_id=objective_id,
            mastery_before=mastery_before,
            mastery_after=self._clamp(mastery_after)
        )

    def _posterior_after_observation(self, *, p_mastery: float, is_correct: bool) -> float:
        if is_correct:
            numerator = p_mastery * (1 - self.p_slip)
            denominator = numerator + (1 - p_mastery) * self.p_guess
        else:
            numerator = p_mastery * self.p_slip
            denominator = numerator + (1 - p_mastery) * (1 - self.p_guess)

        if denominator == 0:
            return p_mastery
        
        return numerator / denominator
    
    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))