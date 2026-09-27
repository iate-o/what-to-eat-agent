# Product Iteration 2 - Personal Food Decision Agent

## Product goal

Move from a one-shot recipe recommender to a small decision system that keeps pantry state during a browser session, replans after feedback, and makes failure modes measurable.

## User pain points

1. Pantry inventory changes after cooking, but one-shot assistants forget it.
2. Users often reject a recommendation for qualitative reasons such as "too slow" or "no mushrooms" and expect the next result to inherit that feedback.
3. Aggregate accuracy does not explain why the workflow fails, which makes iteration difficult.

## Prioritisation

- P0: session pantry state and deterministic consumption updates
- P0: feedback-driven replanning and inherited constraints
- P0: failure taxonomy for evaluation
- Later: account-level persistence, expiry dates, verified nutrition, grocery integrations

## Workflow

Pantry state -> constraints -> generate candidates -> deterministic validation -> retry once if all fail -> score/rank -> pantry-aware shopping list -> user feedback -> replan. After the user confirms cooking, known compatible quantities are deducted from pantry state.

## Guardrails

Inventory deductions occur only when both quantities are known and units are safely comparable. Unknown or incompatible quantities remain unchanged and return a warning. Allergy checking remains a product guardrail, not medical assurance.

## Metrics

Core quality: validity accuracy, constraint compliance, pantry utilisation, missing ingredient count, shopping-list precision/recall/exact match.

Iteration diagnostics: failure taxonomy by allergy, diet, dislike, time, structure and pantry feasibility; replan success against the updated constraint; deterministic inventory deduction coverage.
