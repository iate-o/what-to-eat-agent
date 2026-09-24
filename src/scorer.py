"""Transparent, deterministic scoring and ranking."""

from __future__ import annotations

from .ingredient_matcher import match_ingredients
from .models import (
    IngredientMatch,
    PantryItem,
    RecipeCandidate,
    RecipeScore,
    ScoredRecipe,
    UserConstraints,
    ValidationResult,
)


STAPLES = {"salt", "pepper", "water", "cooking oil", "oil"}


def pantry_utilisation_rate(recipe: RecipeCandidate, pantry: list[PantryItem]) -> float:
    """Share of non-trivial pantry ingredients used by the recipe."""
    relevant = {item.normalized_name for item in pantry if item.normalized_name not in STAPLES}
    if not relevant:
        return 0.0
    used = {
        ingredient.normalized_name
        for ingredient in recipe.ingredients
        if ingredient.normalized_name in relevant
    }
    return len(used) / len(relevant)


def _complexity(recipe: RecipeCandidate) -> tuple[str, float]:
    work = len(recipe.ingredients) + len(recipe.instructions)
    if work <= 10:
        return "low", 1.0
    if work <= 16:
        return "medium", 0.6
    return "high", 0.25


def score_recipe(
    recipe: RecipeCandidate,
    validation: ValidationResult,
    pantry: list[PantryItem],
    constraints: UserConstraints,
    matches: list[IngredientMatch] | None = None,
) -> RecipeScore:
    matches = matches or match_ingredients(recipe.ingredients, pantry)
    required_matches = [
        match for match in matches if not match.required_ingredient.optional
    ]
    missing_count = sum(
        match.status in {"missing", "partially_available"} for match in required_matches
    )
    missing_score = 1 - (missing_count / max(1, len(required_matches)))
    utilisation = pantry_utilisation_rate(recipe, pantry)
    compliance_flags = (
        validation.allergy_safe,
        validation.diet_compliant,
        validation.within_time_limit,
        recipe.servings == constraints.servings,
    )
    compliance = sum(compliance_flags) / len(compliance_flags)
    time_fit = max(
        0.0,
        min(1.0, 1 - recipe.cooking_time_minutes / max(1, constraints.max_cooking_time_minutes)),
    )
    complexity, simplicity = _complexity(recipe)
    final = 100 * (
        utilisation * 0.40
        + missing_score * 0.25
        + compliance * 0.20
        + time_fit * 0.10
        + simplicity * 0.05
    )
    explanation = (
        f"Uses {utilisation:.0%} of relevant pantry items and needs "
        f"{missing_count} ingredient{'s' if missing_count != 1 else ''}."
    )
    return RecipeScore(
        pantry_utilisation_rate=utilisation,
        missing_ingredient_count=missing_count,
        constraint_compliance=compliance,
        cooking_time_fit=time_fit,
        estimated_complexity=complexity,  # type: ignore[arg-type]
        final_score=round(final, 1),
        explanation=explanation,
    )


def rank_recipes(
    recipes: list[tuple[RecipeCandidate, ValidationResult]],
    pantry: list[PantryItem],
    constraints: UserConstraints,
) -> list[ScoredRecipe]:
    scored: list[ScoredRecipe] = []
    for recipe, validation in recipes:
        matches = match_ingredients(recipe.ingredients, pantry)
        scored.append(
            ScoredRecipe(
                recipe=recipe,
                validation=validation,
                score=score_recipe(recipe, validation, pantry, constraints, matches),
                matches=matches,
            )
        )
    return sorted(scored, key=lambda item: item.score.final_score, reverse=True)
