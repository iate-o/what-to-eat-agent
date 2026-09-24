from src.models import RecipeCandidate, RecipeIngredient, UserConstraints
from src.pantry import parse_pantry
from src.validator import validate_recipe


def recipe(*ingredients: str, minutes: int = 20) -> RecipeCandidate:
    return RecipeCandidate(
        title="Dinner",
        servings=2,
        cooking_time_minutes=minutes,
        ingredients=[RecipeIngredient(name=name, normalized_name=name) for name in ingredients],
        instructions=["Cook everything safely.", "Serve."],
    )


def test_allergy_is_a_hard_constraint() -> None:
    result = validate_recipe(
        recipe("tofu", "peanut oil"),
        UserConstraints(allergies=["peanut"]),
        parse_pantry("tofu\npeanut oil"),
    )
    assert result.valid is False
    assert result.allergy_safe is False


def test_allergen_family_is_expanded() -> None:
    result = validate_recipe(
        recipe("tomato", "cream"),
        UserConstraints(allergies=["dairy"]),
        parse_pantry("tomato\ncream"),
    )
    assert result.valid is False
    assert result.allergy_safe is False


def test_diet_and_time_are_hard_constraints() -> None:
    result = validate_recipe(
        recipe("chicken", "rice", minutes=45),
        UserConstraints(dietary_preferences=["vegetarian"], max_cooking_time_minutes=30),
        parse_pantry("chicken\nrice"),
    )
    assert result.diet_compliant is False
    assert result.within_time_limit is False


def test_valid_recipe_passes() -> None:
    result = validate_recipe(
        recipe("tofu", "spinach"),
        UserConstraints(dietary_preferences=["vegan"]),
        parse_pantry("tofu\nspinach"),
    )
    assert result.valid is True
