"""Run the fixed, offline evaluation set without an API key."""

from __future__ import annotations

import json
from pathlib import Path

from src.ingredient_matcher import match_ingredients
from src.models import RecipeCandidate, RecipeIngredient, UserConstraints
from src.pantry import normalize_ingredient, parse_pantry
from src.scorer import score_recipe
from src.shopping_list import build_shopping_list
from src.validator import validate_recipe


def safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def main() -> None:
    cases = json.loads((Path(__file__).parent / "test_cases.json").read_text())
    validity_correct = 0
    recommendation_count = 0
    utilisation: list[float] = []
    compliance: list[float] = []
    missing_counts: list[int] = []
    shopping_precision: list[float] = []
    shopping_recall: list[float] = []
    shopping_exact: list[bool] = []
    results: list[dict[str, object]] = []

    for case in cases:
        pantry = parse_pantry(case["pantry"])
        if case["type"] == "recommendation":
            recommendation_count += 1
            constraints = UserConstraints.model_validate(case["constraints"])
            recipe = RecipeCandidate.model_validate(case["recipe"])
            for ingredient in recipe.ingredients:
                ingredient.normalized_name = normalize_ingredient(
                    ingredient.normalized_name or ingredient.name
                )
            validation = validate_recipe(recipe, constraints, pantry)
            score = score_recipe(recipe, validation, pantry, constraints)
            correct = validation.valid == case["expected_valid"]
            validity_correct += int(correct)
            utilisation.append(score.pantry_utilisation_rate)
            compliance.append(score.constraint_compliance)
            missing_counts.append(score.missing_ingredient_count)
            results.append(
                {
                    "id": case["id"],
                    "valid": validation.valid,
                    "expected_valid": case["expected_valid"],
                    "correct": correct,
                    "constraint_compliance": score.constraint_compliance,
                    "pantry_utilisation": score.pantry_utilisation_rate,
                    "missing_ingredients": score.missing_ingredient_count,
                }
            )
        else:
            ingredients = [RecipeIngredient.model_validate(item) for item in case["ingredients"]]
            matches = match_ingredients(ingredients, pantry)
            shopping = build_shopping_list(matches)
            predicted = {item.ingredient for item in shopping.to_buy}
            expected = set(case["expected_missing"])
            true_positive = len(predicted & expected)
            precision = safe_ratio(true_positive, len(predicted))
            recall = safe_ratio(true_positive, len(expected))
            exact = predicted == expected
            shopping_precision.append(precision)
            shopping_recall.append(recall)
            shopping_exact.append(exact)
            results.append(
                {
                    "id": case["id"],
                    "predicted_missing": sorted(predicted),
                    "expected_missing": sorted(expected),
                    "precision": precision,
                    "recall": recall,
                    "exact_match": exact,
                    "uncertain_matches": len(shopping.uncertain),
                }
            )

    summary = {
        "cases": len(cases),
        "recipe_validity_accuracy": safe_ratio(validity_correct, recommendation_count),
        "average_pantry_utilisation": sum(utilisation) / len(utilisation),
        "average_constraint_compliance": sum(compliance) / len(compliance),
        "average_missing_ingredient_count": sum(missing_counts) / len(missing_counts),
        "shopping_precision": sum(shopping_precision) / len(shopping_precision),
        "shopping_recall": sum(shopping_recall) / len(shopping_recall),
        "shopping_exact_match": sum(shopping_exact) / len(shopping_exact),
        "user_satisfaction": "Not measured; requires real user feedback",
    }
    print(json.dumps({"summary": summary, "results": results}, indent=2))


if __name__ == "__main__":
    main()
