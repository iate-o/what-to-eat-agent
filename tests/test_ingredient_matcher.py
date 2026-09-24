from src.ingredient_matcher import match_ingredient
from src.models import RecipeIngredient
from src.pantry import parse_pantry


def test_partial_quantity_with_unit_conversion() -> None:
    pantry = parse_pantry("300g chicken breast")
    required = RecipeIngredient(name="chicken", normalized_name="chicken", quantity=0.5, unit="kg")
    match = match_ingredient(required, pantry)
    assert match.status == "partially_available"
    assert match.quantity_missing == 0.2
    assert match.unit == "kg"


def test_unknown_quantity_is_not_fabricated() -> None:
    pantry = parse_pantry("rice")
    required = RecipeIngredient(name="rice", normalized_name="rice", quantity=200, unit="g")
    match = match_ingredient(required, pantry)
    assert match.status == "uncertain"
    assert match.quantity_missing is None


def test_incompatible_units_are_uncertain() -> None:
    pantry = parse_pantry("2 cups spinach")
    required = RecipeIngredient(name="spinach", normalized_name="spinach", quantity=100, unit="g")
    assert match_ingredient(required, pantry).status == "uncertain"
