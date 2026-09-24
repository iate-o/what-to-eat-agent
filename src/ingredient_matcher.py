"""Deterministic pantry-to-recipe ingredient matching."""

from __future__ import annotations

from .models import IngredientMatch, PantryItem, RecipeIngredient
from .pantry import normalize_ingredient, normalize_unit


CONVERSIONS: dict[str, tuple[str, float]] = {
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "tsp": ("volume", 5.0),
    "tbsp": ("volume", 15.0),
    "cup": ("volume", 250.0),
    "count": ("count", 1.0),
}


def _base_quantity(quantity: float, unit: str) -> tuple[str, float] | None:
    conversion = CONVERSIONS.get(unit)
    if not conversion:
        return None
    family, multiplier = conversion
    return family, quantity * multiplier


def match_ingredient(required: RecipeIngredient, pantry: list[PantryItem]) -> IngredientMatch:
    normalized = normalize_ingredient(required.normalized_name or required.name)
    required.normalized_name = normalized
    candidate = next((item for item in pantry if item.normalized_name == normalized), None)
    if candidate is None:
        return IngredientMatch(
            required_ingredient=required,
            status="missing",
            quantity_required=required.quantity,
            unit=normalize_unit(required.unit),
            confidence=1.0,
            note="No matching pantry item",
        )

    req_unit = normalize_unit(required.unit)
    pantry_unit = normalize_unit(candidate.unit)
    if candidate.ambiguous:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="uncertain",
            quantity_required=required.quantity,
            quantity_available=candidate.quantity,
            unit=req_unit,
            confidence=0.5,
            note="The pantry name is ambiguous; confirm the exact ingredient",
        )

    if required.quantity is None:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="available",
            quantity_available=candidate.quantity,
            unit=pantry_unit,
            confidence=0.9,
            note="Matched by ingredient presence",
        )

    if candidate.quantity is None:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="uncertain",
            quantity_required=required.quantity,
            unit=req_unit,
            confidence=0.65,
            note="Ingredient is present but the available quantity is unknown",
        )

    if not req_unit or not pantry_unit:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="uncertain",
            quantity_required=required.quantity,
            quantity_available=candidate.quantity,
            unit=req_unit,
            confidence=0.55,
            note="Cannot compare quantities because a unit is missing",
        )

    req_base = _base_quantity(required.quantity, req_unit)
    pantry_base = _base_quantity(candidate.quantity, pantry_unit)
    if not req_base or not pantry_base or req_base[0] != pantry_base[0]:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="uncertain",
            quantity_required=required.quantity,
            quantity_available=candidate.quantity,
            unit=req_unit,
            confidence=0.4,
            note=f"Cannot safely compare {pantry_unit} with {req_unit}",
        )

    if pantry_base[1] >= req_base[1]:
        return IngredientMatch(
            required_ingredient=required,
            pantry_match=candidate,
            status="available",
            quantity_required=required.quantity,
            quantity_available=candidate.quantity,
            unit=req_unit,
            confidence=1.0,
        )

    missing_base = req_base[1] - pantry_base[1]
    missing_in_required_unit = missing_base / CONVERSIONS[req_unit][1]
    return IngredientMatch(
        required_ingredient=required,
        pantry_match=candidate,
        status="partially_available",
        quantity_required=required.quantity,
        quantity_available=candidate.quantity,
        quantity_missing=round(missing_in_required_unit, 3),
        unit=req_unit,
        confidence=1.0,
        note="Pantry quantity is below the recipe requirement",
    )


def match_ingredients(
    ingredients: list[RecipeIngredient], pantry: list[PantryItem]
) -> list[IngredientMatch]:
    return [match_ingredient(ingredient, pantry) for ingredient in ingredients]
