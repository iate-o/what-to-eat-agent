"""Extract structured recipe fields from pasted text."""

from __future__ import annotations

from .llm_client import LLMClient, load_prompt
from .models import ParsedRecipe
from .pantry import normalize_ingredient, normalize_unit


def parse_recipe_text(client: LLMClient, recipe_text: str) -> ParsedRecipe:
    prompt = load_prompt("parse_recipe.txt", recipe_text=recipe_text)
    recipe = client.parse(prompt, ParsedRecipe)
    for ingredient in recipe.ingredients:
        ingredient.normalized_name = normalize_ingredient(
            ingredient.normalized_name or ingredient.name
        )
        ingredient.unit = normalize_unit(ingredient.unit)
    if not recipe.instructions:
        recipe.warnings.append("No cooking instructions were found in the pasted text.")
    if not recipe.ingredients:
        recipe.warnings.append("No ingredients were confidently extracted.")
    return recipe
