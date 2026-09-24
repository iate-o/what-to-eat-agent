"""Single-agent workflow coordinating generation, validation, ranking, and replanning."""

from __future__ import annotations

from .feedback import apply_feedback, interpret_feedback
from .ingredient_matcher import match_ingredients
from .llm_client import LLMClient
from .models import CookResult, UserConstraints
from .pantry import parse_pantry
from .recipe_generator import generate_recipe_candidates
from .scorer import rank_recipes
from .shopping_list import build_shopping_list
from .validator import validate_recipe


class WorkflowError(RuntimeError):
    """A user-actionable workflow failure."""


def cook_from_pantry(
    client: LLMClient,
    pantry_text: str,
    constraints: UserConstraints,
    feedback: str | None = None,
) -> CookResult:
    pantry = parse_pantry(pantry_text)
    if not pantry:
        raise WorkflowError("Add at least one pantry ingredient before finding recipes.")
    if feedback:
        constraints = apply_feedback(constraints, interpret_feedback(client, feedback))

    candidates = []
    evaluated = []
    retries = 0
    validation_feedback: list[str] = []
    for attempt in range(2):
        retries = attempt
        candidates = generate_recipe_candidates(
            client, pantry, constraints, validation_feedback if attempt else None
        )
        evaluated = [
            (candidate, validate_recipe(candidate, constraints, pantry))
            for candidate in candidates
        ]
        if any(validation.valid for _, validation in evaluated):
            break
        validation_feedback = [
            issue
            for _, validation in evaluated
            for issue in validation.issues
        ]

    valid = [(recipe, validation) for recipe, validation in evaluated if validation.valid]
    invalid = [(recipe, validation) for recipe, validation in evaluated if not validation.valid]
    if not valid:
        details = "; ".join(dict.fromkeys(validation_feedback))
        raise WorkflowError(
            "I couldn't find a safe recipe after one retry. "
            f"The tightest constraints were: {details or 'the current pantry and preferences'}."
        )

    ranked = rank_recipes(valid, pantry, constraints)
    rejected = rank_recipes(invalid, pantry, constraints)
    best = ranked[0]
    shopping = build_shopping_list(best.matches)
    trace = [
        f"Parsed {len(pantry)} pantry ingredients",
        (
            f"Applied constraints: {constraints.servings} servings, under "
            f"{constraints.max_cooking_time_minutes} min"
        ),
        f"Generated {len(candidates)} candidate recipes" + (" after one retry" if retries else ""),
        f"Removed {len(invalid)} candidate(s) that failed validation",
        f"Ranked {len(ranked)} valid candidate(s) with deterministic weights",
        f"Selected {best.recipe.title}",
        f"Pantry utilisation: {best.score.pantry_utilisation_rate:.0%}",
        f"Missing ingredients: {best.score.missing_ingredient_count}",
    ]
    return CookResult(
        best_match=best,
        other_candidates=ranked[1:],
        rejected_candidates=rejected,
        shopping_list=shopping,
        constraints=constraints,
        pantry=pantry,
        trace=trace,
    )
