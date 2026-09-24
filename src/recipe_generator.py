"""Structured candidate generation; ranking happens elsewhere."""

from __future__ import annotations

import json

from .llm_client import LLMClient, load_prompt
from .models import PantryItem, RecipeCandidate, RecipeCandidateBatch, UserConstraints
from .pantry import normalize_ingredient, normalize_unit


def generate_recipe_candidates(
    client: LLMClient,
    pantry: list[PantryItem],
    constraints: UserConstraints,
    validation_feedback: list[str] | None = None,
) -> list[RecipeCandidate]:
    prompt = load_prompt(
        "generate_recipes.txt",
        pantry_json=json.dumps([item.model_dump() for item in pantry], indent=2),
        constraints_json=constraints.model_dump_json(indent=2),
        validation_feedback=json.dumps(validation_feedback or []),
    )
    batch = client.parse(prompt, RecipeCandidateBatch)
    for recipe in batch.recipes:
        for ingredient in recipe.ingredients:
            ingredient.normalized_name = normalize_ingredient(
                ingredient.normalized_name or ingredient.name
            )
            ingredient.unit = normalize_unit(ingredient.unit)
    return batch.recipes[:3]
