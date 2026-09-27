from src.models import RecipeCandidate,RecipeIngredient
from src.pantry import parse_pantry
from src.pantry_state import consume_recipe,merge_pantry,pantry_to_text
def test_merge_pantry_adds_compatible_quantities():
    [chicken]=merge_pantry(parse_pantry("300g chicken breast"),parse_pantry("200g chicken breast"));assert chicken.normalized_name=="chicken" and chicken.quantity==500
def test_consume_recipe_deducts_known_quantities_and_removes_empty_items():
    pantry=parse_pantry("500g chicken breast\n2 eggs");recipe=RecipeCandidate(title="Chicken",servings=2,cooking_time_minutes=20,ingredients=[RecipeIngredient(name="chicken",normalized_name="chicken",quantity=300,unit="g"),RecipeIngredient(name="eggs",normalized_name="egg",quantity=2,unit="count")],instructions=["Cook."]);updated,warnings=consume_recipe(pantry,recipe);assert warnings==[] and next(i for i in updated if i.normalized_name=="chicken").quantity==200 and not any(i.normalized_name=="egg" for i in updated) and "200g" in pantry_to_text(updated)
