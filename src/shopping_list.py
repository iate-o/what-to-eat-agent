"""Build a reusable, deterministic shopping list from ingredient matches."""

from __future__ import annotations

from .models import IngredientMatch, ShoppingList, ShoppingListItem


def build_shopping_list(matches: list[IngredientMatch]) -> ShoppingList:
    result = ShoppingList()
    buckets = {
        "available": result.available,
        "partially_available": result.partial,
        "missing": result.missing,
        "uncertain": result.uncertain,
    }
    for match in matches:
        buckets[match.status].append(match)

    aggregated: dict[tuple[str, str | None, str], float | None] = {}
    for match in [*result.partial, *result.missing]:
        ingredient = match.required_ingredient.normalized_name or match.required_ingredient.name
        quantity = match.quantity_missing if match.status == "partially_available" else match.quantity_required
        reason = "Top up pantry quantity" if match.status == "partially_available" else "Not in pantry"
        key = (ingredient, match.unit, reason)
        if key not in aggregated:
            aggregated[key] = quantity
        elif aggregated[key] is not None and quantity is not None:
            aggregated[key] = aggregated[key] + quantity  # type: ignore[operator]
        else:
            aggregated[key] = None

    result.to_buy = [
        ShoppingListItem(ingredient=name, quantity=quantity, unit=unit, reason=reason)
        for (name, unit, reason), quantity in sorted(aggregated.items())
    ]
    return result
