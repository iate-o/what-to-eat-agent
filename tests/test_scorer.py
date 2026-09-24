from src.models import RecipeCandidate, RecipeIngredient, UserConstraints
from src.pantry import parse_pantry
from src.scorer import pantry_utilisation_rate, rank_recipes
from src.validator import validate_recipe


def make_recipe(title: str, ingredients: list[str]) -> RecipeCandidate:
    return RecipeCandidate(
        title=title,
        servings=2,
        cooking_time_minutes=20,
        ingredients=[RecipeIngredient(name=name, normalized_name=name) for name in ingredients],
        instructions=["Prepare.", "Cook.", "Serve."],
    )


def test_utilisation_ignores_trivial_staples() -> None:
    pantry = parse_pantry("chicken\nspinach\nsalt\nwater")
    candidate = make_recipe("Chicken", ["chicken", "salt"])
    assert pantry_utilisation_rate(candidate, pantry) == 0.5


def test_candidate_using_more_pantry_ranks_higher() -> None:
    pantry = parse_pantry("chicken\nspinach\nrice\nmushroom")
    constraints = UserConstraints()
    strong = make_recipe("Pantry bowl", ["chicken", "spinach", "rice", "onion"])
    weak = make_recipe("Other bowl", ["chicken", "avocado", "lime", "tomato"])
    evaluated = [
        (strong, validate_recipe(strong, constraints, pantry)),
        (weak, validate_recipe(weak, constraints, pantry)),
    ]
    ranked = rank_recipes(evaluated, pantry, constraints)
    assert ranked[0].recipe.title == "Pantry bowl"
    assert ranked[0].score.final_score > ranked[1].score.final_score


def test_partial_quantity_counts_as_an_item_to_buy() -> None:
    pantry = parse_pantry("300g chicken breast")
    constraints = UserConstraints()
    candidate = RecipeCandidate(
        title="Chicken",
        servings=2,
        cooking_time_minutes=20,
        ingredients=[
            RecipeIngredient(name="chicken", normalized_name="chicken", quantity=500, unit="g")
        ],
        instructions=["Cook through.", "Serve."],
    )
    validation = validate_recipe(candidate, constraints, pantry)
    [ranked] = rank_recipes([(candidate, validation)], pantry, constraints)
    assert ranked.score.missing_ingredient_count == 1
