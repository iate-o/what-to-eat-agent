from src.models import RecipeCandidate, RecipeCandidateBatch, RecipeIngredient, UserConstraints
from src.orchestrator import cook_from_pantry


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def parse(self, prompt, schema):
        self.calls += 1
        if self.calls == 1:
            return RecipeCandidateBatch(
                recipes=[candidate("Unsafe", ["peanut", "rice"], minutes=45)]
            )
        return RecipeCandidateBatch(
            recipes=[
                candidate("Fast rice bowl", ["rice", "spinach"], minutes=15),
                candidate("Egg rice", ["rice", "egg"], minutes=20),
            ]
        )


def candidate(title: str, ingredients: list[str], minutes: int) -> RecipeCandidate:
    return RecipeCandidate(
        title=title,
        servings=2,
        cooking_time_minutes=minutes,
        ingredients=[RecipeIngredient(name=name, normalized_name=name) for name in ingredients],
        instructions=["Cook.", "Serve."],
    )


def test_retries_once_then_returns_ranked_result() -> None:
    client = FakeClient()
    result = cook_from_pantry(
        client,  # type: ignore[arg-type]
        "rice\nspinach\negg",
        UserConstraints(max_cooking_time_minutes=30, allergies=["peanut"]),
    )
    assert client.calls == 2
    assert result.best_match.recipe.title == "Fast rice bowl"
    assert "after one retry" in result.trace[2]
