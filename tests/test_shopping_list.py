from src.ingredient_matcher import match_ingredients
from src.models import RecipeIngredient
from src.pantry import parse_pantry
from src.shopping_list import build_shopping_list


def test_builds_partial_and_missing_list() -> None:
    pantry = parse_pantry("300g chicken breast\n4 eggs\n200g spinach")
    ingredients = [
        RecipeIngredient(name="chicken", normalized_name="chicken", quantity=500, unit="g"),
        RecipeIngredient(name="eggs", normalized_name="egg", quantity=2, unit="count"),
        RecipeIngredient(name="spinach", normalized_name="spinach", quantity=200, unit="g"),
        RecipeIngredient(name="onion", normalized_name="onion", quantity=1, unit="count"),
    ]
    shopping = build_shopping_list(match_ingredients(ingredients, pantry))
    assert {match.required_ingredient.normalized_name for match in shopping.available} == {"egg", "spinach"}
    assert shopping.partial[0].quantity_missing == 200
    assert {item.ingredient for item in shopping.to_buy} == {"chicken", "onion"}


def test_deduplicates_missing_ingredients() -> None:
    ingredients = [
        RecipeIngredient(name="onion", normalized_name="onion", quantity=1, unit="count"),
        RecipeIngredient(name="onion", normalized_name="onion", quantity=2, unit="count"),
    ]
    shopping = build_shopping_list(match_ingredients(ingredients, []))
    assert len(shopping.to_buy) == 1
    assert shopping.to_buy[0].quantity == 3
