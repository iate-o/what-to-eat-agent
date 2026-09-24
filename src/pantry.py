"""Small, deterministic ingredient and pantry normalizer."""

from __future__ import annotations

import re

from .models import PantryItem


ALIASES = {
    "chicken breast": "chicken",
    "chicken breasts": "chicken",
    "scallion": "green onion",
    "scallions": "green onion",
    "spring onion": "green onion",
    "spring onions": "green onion",
    "bell pepper": "capsicum",
    "bell peppers": "capsicum",
    "garbanzo bean": "chickpea",
    "garbanzo beans": "chickpea",
    "chickpeas": "chickpea",
    "eggs": "egg",
    "tomatoes": "tomato",
    "potatoes": "potato",
    "mushrooms": "mushroom",
    "onions": "onion",
}

AMBIGUOUS_INGREDIENTS = {"cream", "stock", "flour", "oil", "cheese", "milk"}

UNIT_ALIASES = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "l": "l",
    "litre": "l",
    "litres": "l",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "cup": "cup",
    "cups": "cup",
    "piece": "count",
    "pieces": "count",
    "item": "count",
    "items": "count",
}

_LEADING_QUANTITY = re.compile(
    r"^\s*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ml|l|tsp|tbsp|cups?|grams?|kilograms?|pieces?|items?)?\s+(?P<name>.+)$",
    re.IGNORECASE,
)
_TRAILING_QUANTITY = re.compile(
    r"^\s*(?P<name>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ml|l|tsp|tbsp|cups?|grams?|kilograms?|pieces?|items?)?\s*$",
    re.IGNORECASE,
)


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    return UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def normalize_ingredient(name: str) -> str:
    """Normalize common variants without pretending to be a full ontology."""
    value = re.sub(r"[^a-z0-9\s-]", "", name.lower()).strip()
    value = re.sub(r"\s+", " ", value)
    if value in ALIASES:
        return ALIASES[value]
    if value.endswith("ies") and len(value) > 4:
        value = f"{value[:-3]}y"
    elif value.endswith("s") and not value.endswith(("ss", "us")) and len(value) > 3:
        value = value[:-1]
    return ALIASES.get(value, value)


def parse_pantry_line(line: str) -> PantryItem | None:
    cleaned = line.strip().lstrip("-•").strip()
    if not cleaned:
        return None

    match = _LEADING_QUANTITY.match(cleaned) or _TRAILING_QUANTITY.match(cleaned)
    if match:
        name = match.group("name").strip()
        quantity = float(match.group("qty"))
        unit = normalize_unit(match.group("unit"))
        if unit is None and normalize_ingredient(name) in {"egg", "onion", "capsicum"}:
            unit = "count"
    else:
        name, quantity, unit = cleaned, None, None

    normalized = normalize_ingredient(name)
    return PantryItem(
        name=name,
        normalized_name=normalized,
        quantity=quantity,
        unit=unit,
        ambiguous=normalized in AMBIGUOUS_INGREDIENTS,
    )


def parse_pantry(text: str) -> list[PantryItem]:
    """Parse newline- or comma-separated pantry text and merge exact duplicates."""
    items: dict[tuple[str, str | None], PantryItem] = {}
    for part in re.split(r"[\n,;]+", text):
        item = parse_pantry_line(part)
        if not item:
            continue
        key = (item.normalized_name, item.unit)
        existing = items.get(key)
        if existing and existing.quantity is not None and item.quantity is not None:
            existing.quantity += item.quantity
        elif not existing:
            items[key] = item
    return list(items.values())
