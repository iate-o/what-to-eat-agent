# Personal Food Decision Agent - Iteration 2

A pantry-aware AI decision product that helps users decide what to cook, adapts to constraints and feedback, and turns recipe choices into pantry and shopping actions.

## What changed

- Session pantry state in Streamlit
- Deterministic inventory deduction after the user confirms cooking
- Feedback-driven replanning with inherited constraints
- Explicit failure taxonomy for allergy, diet, dislike, time, structure and pantry feasibility
- Deterministic validation and ranking around structured LLM output

## Product logic

The LLM is used for ambiguous language tasks such as recipe generation, recipe extraction and open-ended feedback. Deterministic Python code handles allergy and diet checks, cooking-time validation, pantry matching, compatible quantity comparison, ranking, shopping-list construction and inventory updates.

The workflow is intentionally controlled:

Pantry state → constraints → generate candidates → validate → retry once if all fail → score and rank → shopping list → feedback → replan → optional post-cooking pantry update.

## Verified offline results

- 20 automated tests passed
- 12 offline product fixtures
- Recipe-validity accuracy: 100%
- Average pantry utilisation: 86.1%
- Average constraint compliance: 86.1%
- Average missing ingredient count: 0.44
- Shopping precision / recall / exact match: 100% / 100% / 100%

These are results for the checked-in offline deterministic fixtures, not production or live-model benchmarks.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Tests and evaluation:

```bash
pytest
python -m evals.run_evals
```

See `docs/product_iteration_2.md` and `docs/portfolio_notes.md` for product framing and interview notes.
