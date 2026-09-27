# Portfolio notes - Iteration 2

## Resume-ready framing

- Framed and built a pantry-aware AI decision product around the recurring problem "what can I cook with what I already have?", prioritising recipe recommendation and recipe-to-shopping-list as the first two MVP journeys.
- Designed a controlled Agent workflow where the LLM generates or extracts structured candidates while deterministic Python validates allergies, diet, time and pantry feasibility, ranks options, handles quantities, and replans from feedback.
- Added session pantry state, deterministic post-cooking inventory deduction, explicit uncertainty states, and a stable failure taxonomy. The project now has 20 automated tests and a 12-case offline evaluation suite.

## Product chain

Problem → user journey → prioritisation → AI/non-AI responsibility split → structured workflow → MVP → offline evaluation → failure taxonomy → pantry-state iteration → next live-model experiment.

## 30-second interview version

I started from a simple user problem: people have ingredients at home but still spend time deciding what to cook and often buy ingredients they already have. I prioritised two MVP journeys: generate a suitable meal from the pantry, and turn a recipe into a pantry-aware shopping list. The model handles generation and extraction, while deterministic code validates hard constraints, ranks candidates and performs quantity comparisons. In Iteration 2 I added session pantry state, inventory deduction after cooking, feedback-driven replanning and a failure taxonomy so I could understand not only whether the workflow worked, but why it failed.

## Evidence

The checked-in offline suite contains 12 product fixtures and currently reports 100% recipe-validity accuracy, 86.1% average pantry utilisation, and 100% shopping-list exact match. These numbers describe the deterministic fixture set only. Do not present them as production or live-model performance.

## Next experiment

Run repeated live generations against a pinned model and prompt version, review every hard-constraint failure, and compare prompt/workflow iterations using the same case set.
