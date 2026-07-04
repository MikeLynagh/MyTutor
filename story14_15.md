# Story 14 + 15 Implementation Guide

Goal: add in-memory learner mastery state and update it after answer evaluation.

This guide is intentionally written so you can type the implementation yourself.

## What You Are Building

You already have this flow:

```text
lesson page
  -> POST /api/missions/{mission_id}/answers
  -> EvaluatorAgent returns EvaluationResult
  -> frontend displays feedback
```

Stories 14 and 15 add this:

```text
EvaluationResult
  -> MasteryTracker updates objective mastery
  -> memory store saves updated learner state
  -> /answers returns evaluation + mastery update
```

Do not add next action routing yet. That is Story 16.

---

## Design Boundary

Keep these responsibilities separate:

```text
EvaluatorAgent
  Decides how good the submitted answer is.

MasteryTracker
  Converts evaluation evidence into a mastery probability update.

MemoryStore
  Stores and retrieves per-mission mastery state.

/answers endpoint
  Coordinates evaluation, mastery update, and response.
```

This separation matters because later you can improve the mastery formula without touching the LLM evaluator, and you can improve the evaluator without rewriting learner memory.

---

## Step 1: Add Learner State Models

File:

```text
backend/app/models/learner.py
```

Replace or create the file with:

```python
from pydantic import BaseModel, Field


class ObjectiveMasteryState(BaseModel):
    objective_id: str
    p_mastery: float = Field(default=0.1, ge=0, le=1)
    attempts: int = Field(default=0, ge=0)
    recent_errors: list[str] = Field(default_factory=list)
    last_feedback: str | None = None


class MissionLearnerState(BaseModel):
    mission_id: str
    objectives: dict[str, ObjectiveMasteryState] = Field(default_factory=dict)
```

Explanation:

`p_mastery` is a probability from `0` to `1`.

It is not a grade. It means:

```text
How likely is it that the learner currently knows this objective?
```

Start at `0.1` because the app assumes the learner is a beginner unless evidence says otherwise.

---

## Step 2: Extend MemoryStore

File:

```text
backend/app/models/memory_store.py
```

Add this import:

```python
from app.models.learner import MissionLearnerState, ObjectiveMasteryState
```

Inside `MemoryStore.__init__`, add:

```python
self._learner_states: dict[str, MissionLearnerState] = {}
```

Then add these methods to `MemoryStore`:

```python
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
```

Explanation:

These methods lazily create learner state when needed. That keeps earlier stories simple because you do not need to initialize mastery state during mission creation.

---

## Step 3: Add Mastery Update Schema

File:

```text
backend/app/schemas/mastery.py
```

You may already have this. Confirm it exists:

```python
class MasteryUpdate(BaseModel):
    objective_id: str
    mastery_before: float = Field(ge=0, le=1)
    mastery_after: float = Field(ge=0, le=1)
```

No change is needed if it already exists.

---

## Step 4: Implement Thresholded BKT MasteryTracker

File:

```text
backend/app/services/mastery_tracker.py
```

Add:

```python
from app.schemas.mastery import MasteryUpdate


class MasteryTracker:
    def __init__(
        self,
        *,
        p_learn: float = 0.2,
        p_guess: float = 0.2,
        p_slip: float = 0.1,
        correct_threshold: float = 0.75,
    ) -> None:
        self.p_learn = p_learn
        self.p_guess = p_guess
        self.p_slip = p_slip
        self.correct_threshold = correct_threshold

    def update(
        self,
        *,
        objective_id: str,
        current_mastery: float,
        score: float,
    ) -> MasteryUpdate:
        is_correct = score >= self.correct_threshold
        mastery_before = self._clamp(current_mastery)
        posterior = self._posterior_after_observation(
            p_mastery=mastery_before,
            is_correct=is_correct,
        )
        mastery_after = posterior + (1 - posterior) * self.p_learn

        return MasteryUpdate(
            objective_id=objective_id,
            mastery_before=mastery_before,
            mastery_after=self._clamp(mastery_after),
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
```

Explanation:

This is thresholded Bayesian Knowledge Tracing.

The evaluator gives a score from `0` to `1`.

The mastery tracker converts that into binary evidence:

```text
score >= 0.75 -> correct
score < 0.75  -> incorrect
```

Then BKT updates the probability that the learner knows the objective.

Default parameters:

```text
p_learn = 0.20
p_guess = 0.20
p_slip  = 0.10
```

These are MVP defaults, not scientifically calibrated values.

---

## Step 5: Update Answer Response Schema

File:

```text
backend/app/schemas/answer.py
```

You currently have:

```python
class AnswerEvaluationOnlyResponse(BaseModel):
    evaluation: EvaluationResult
```

For Stories 14 + 15, replace it with:

```python
class AnswerEvaluationWithMasteryResponse(BaseModel):
    evaluation: EvaluationResult
    mastery: MasteryUpdate
```

You can keep `AnswerEvaluationOnlyResponse` if you want, but `/answers` should now use the new response.

Explanation:

Do not include `next_action` yet. That belongs to Story 16/17.

---

## Step 6: Update `/answers` Endpoint

File:

```text
backend/app/api/answers.py
```

Add import:

```python
from app.services.mastery_tracker import MasteryTracker
from app.schemas.answer import AnswerEvaluationWithMasteryResponse
```

Near the existing evaluator:

```python
evaluator = EvaluatorAgent()
mastery_tracker = MasteryTracker()
```

Change route response model:

```python
@router.post("/missions/{mission_id}/answers", response_model=AnswerEvaluationWithMasteryResponse)
```

After evaluation:

```python
objective_state = memory_store.get_objective_mastery(
    mission_id=mission_id,
    objective_id=payload.objective_id,
)

mastery = mastery_tracker.update(
    objective_id=payload.objective_id,
    current_mastery=objective_state.p_mastery,
    score=evaluation.score,
)

objective_state.p_mastery = mastery.mastery_after
objective_state.attempts += 1
objective_state.last_feedback = evaluation.feedback
objective_state.recent_errors = [
    error
    for error in [
        evaluation.misconception,
        *evaluation.missing_points,
    ]
    if error
][-5:]

memory_store.save_objective_mastery(
    mission_id=mission_id,
    objective_state=objective_state,
)

return AnswerEvaluationWithMasteryResponse(
    evaluation=evaluation,
    mastery=mastery,
)
```

Explanation:

This records:

```text
current mastery probability
attempt count
recent errors
last feedback
```

`recent_errors[-5:]` keeps the list from growing forever.

---

## Step 7: Update Frontend Types

File:

```text
frontend/my-app/src/types/mission.ts
```

Add:

```ts
export const answerEvaluationWithMasteryResponseSchema = z.object({
  evaluation: evaluationResultSchema,
  mastery: masteryUpdateSchema,
});

export type AnswerEvaluationWithMasteryResponse = z.infer<
  typeof answerEvaluationWithMasteryResponseSchema
>;
```

You can keep `answerEvaluationOnlyResponseSchema` temporarily, but the lesson page should use the new schema.

---

## Step 8: Update Lesson Page Feedback UI

File:

```text
frontend/my-app/app/missions/[missionId]/lesson/page.tsx
```

Change imports:

```ts
import type { AnswerEvaluationWithMasteryResponse, LessonStartResponse, Mission } from "@/types/mission";
import {
  answerEvaluationWithMasteryResponseSchema,
  lessonStartResponseSchema,
  missionSchema,
} from "@/types/mission";
```

Change state:

```ts
const [answerEvaluation, setAnswerEvaluation] =
  React.useState<AnswerEvaluationWithMasteryResponse | null>(null);
```

Change response parsing:

```ts
const evaluation = answerEvaluationWithMasteryResponseSchema.parse(await response.json());
```

In the feedback section, add mastery display:

```tsx
<p className="mt-3 text-sm leading-relaxed text-slate-600">
  <span className="font-medium text-slate-800">Mastery:</span>{" "}
  {Math.round(answerEvaluation.mastery.mastery_before * 100)}% ->{" "}
  {Math.round(answerEvaluation.mastery.mastery_after * 100)}%
</p>
```

Use ASCII `->` in code unless the file already uses arrows.

Explanation:

This makes the adaptive state visible without adding routing yet.

---

## Step 9: Manual Test

Restart backend.

Create a fresh mission.

Generate a lesson.

Submit a weak answer:

```text
Edges have two colours.
```

Expected:

```text
feedback appears
score is less than 100%
missing points appear
mastery changes slightly
```

Submit a strong answer:

```text
Centres have one colour, edges have two colours, and corners have three colours.
```

Expected:

```text
feedback is positive
score is high
mastery increases more
```

---

## Step 10: Checks

Run:

```bash
cd backend
./.venv/bin/python -m compileall app
```

Run:

```bash
cd frontend/my-app
npx tsc --noEmit
npm run lint
```

---

## What Not To Build Yet

Do not implement:

```text
ObjectiveRouter
next_action
advance lesson
progress dashboard changes
database persistence
```

Those are separate stories.

For this step, the endpoint should return:

```json
{
  "evaluation": {},
  "mastery": {}
}
```

Not:

```json
{
  "evaluation": {},
  "mastery": {},
  "next_action": {}
}
```
