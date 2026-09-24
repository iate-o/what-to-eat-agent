"""Hard-constraint validation for generated recipe candidates."""

from __future__ import annotations

from .ingredient_matcher import match_ingredients
from .models import PantryItem, RecipeCandidate, UserConstraints, ValidationResult
from .pantry import normalize_ingredient


DIET_EXCLUSIONS: dict[str, set[str]] = {
    "vegetarian": {
        "chicken", "beef", "pork", "lamb", "turkey", "bacon", "ham", "fish",
        "salmon", "tuna", "prawn", "shrimp", "anchovy", "gelatin",
    },
    "vegan": {
        "chicken", "beef", "pork", "lamb", "turkey", "bacon", "ham", "fish",
        "salmon", "tuna", "prawn", "shrimp", "anchovy", "gelatin", "egg", "milk",
        "cream", "cheese", "butter", "yogurt", "honey", "mayonnaise",
    },
    "keto": {
        "rice", "pasta", "bread", "potato", "sweet potato", "flour", "sugar",
        "noodle", "oat", "quinoa", "couscous", "tortilla",
    },
    "gluten-free": {
        "wheat", "barley", "rye", "bread", "pasta", "flour", "couscous",
        "soy sauce", "breadcrumbs",
    },
    "dairy-free": {"milk", "cream", "cheese", "butter", "yogurt", "whey"},
}

PROTEIN_SOURCES = {
    "chicken", "beef", "pork", "lamb", "turkey", "fish", "salmon", "tuna",
    "prawn", "shrimp", "egg", "tofu", "tempeh", "lentil", "chickpea", "bean",
    "greek yogurt", "cottage cheese", "seitan",
}

ALLERGEN_GROUPS: dict[str, set[str]] = {
    "dairy": {"milk", "cream", "cheese", "butter", "yogurt", "whey", "casein"},
    "milk": {"milk", "cream", "cheese", "butter", "yogurt", "whey", "casein"},
    "egg": {"egg", "mayonnaise"},
    "gluten": {"wheat", "barley", "rye", "bread", "pasta", "flour", "couscous", "soy sauce"},
    "peanut": {"peanut", "groundnut"},
    "shellfish": {"shrimp", "prawn", "crab", "lobster", "crayfish"},
    "tree nut": {"almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia"},
    "nut": {"peanut", "almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia"},
    "fish": {"fish", "salmon", "tuna", "cod", "anchovy", "sardine"},
    "soy": {"soy", "tofu", "tempeh", "edamame", "miso"},
}


def _ingredient_conflicts(ingredient: str, forbidden: set[str]) -> bool:
    normalized = normalize_ingredient(ingredient)
    return any(term == normalized or term in normalized.split() for term in forbidden)


def validate_recipe(
    recipe: RecipeCandidate,
    constraints: UserConstraints,
    pantry: list[PantryItem],
) -> ValidationResult:
    issues: list[str] = []
    names = [ingredient.normalized_name or ingredient.name for ingredient in recipe.ingredients]

    allergy_safe = True
    for allergy in constraints.allergies:
        normalized_allergy = normalize_ingredient(allergy)
        forbidden = ALLERGEN_GROUPS.get(normalized_allergy, {normalized_allergy})
        conflicts = [name for name in names if _ingredient_conflicts(name, forbidden)]
        if conflicts:
            allergy_safe = False
            issues.append(f"Contains allergy conflict: {allergy}")

    diet_compliant = True
    preferences = {preference.strip().lower().replace("_", "-") for preference in constraints.dietary_preferences}
    for preference in preferences:
        forbidden = DIET_EXCLUSIONS.get(preference, set())
        conflicts = [name for name in names if _ingredient_conflicts(name, forbidden)]
        if conflicts:
            diet_compliant = False
            issues.append(f"Conflicts with {preference}: {', '.join(sorted(set(conflicts)))}")
        if preference == "high protein" and not any(
            _ingredient_conflicts(name, PROTEIN_SOURCES) for name in names
        ):
            diet_compliant = False
            issues.append("No clear high-protein ingredient")

    for dislike in constraints.dislikes:
        if any(_ingredient_conflicts(name, {normalize_ingredient(dislike)}) for name in names):
            diet_compliant = False
            issues.append(f"Contains disliked ingredient: {dislike}")

    within_time_limit = 0 < recipe.cooking_time_minutes <= constraints.max_cooking_time_minutes
    if not within_time_limit:
        issues.append(
            f"Cooking time ({recipe.cooking_time_minutes} min) exceeds or omits the "
            f"{constraints.max_cooking_time_minutes}-minute limit"
        )

    structurally_valid = bool(
        recipe.title.strip()
        and recipe.ingredients
        and recipe.instructions
        and all(step.strip() for step in recipe.instructions)
    )
    if not structurally_valid:
        issues.append("Recipe is missing a title, ingredients, or usable instructions")

    required = [ingredient for ingredient in recipe.ingredients if not ingredient.optional]
    matches = match_ingredients(required, pantry)
    absent = sum(match.status == "missing" for match in matches)
    pantry_feasible = not required or absent <= max(3, int(len(required) * 0.6))
    if not pantry_feasible:
        issues.append("Recipe requires too many ingredients not found in the pantry")

    return ValidationResult(
        valid=all(
            (allergy_safe, diet_compliant, within_time_limit, structurally_valid, pantry_feasible)
        ),
        allergy_safe=allergy_safe,
        diet_compliant=diet_compliant,
        within_time_limit=within_time_limit,
        structurally_valid=structurally_valid,
        pantry_feasible=pantry_feasible,
        issues=issues,
    )
