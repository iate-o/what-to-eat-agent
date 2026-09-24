from src.pantry import normalize_ingredient, parse_pantry


def test_normalizes_aliases_and_merges_quantities() -> None:
    pantry = parse_pantry("300g chicken breast\n200 g chicken breasts\n4 eggs\nspring onions")
    chicken = next(item for item in pantry if item.normalized_name == "chicken")
    assert chicken.quantity == 500
    assert chicken.unit == "g"
    assert normalize_ingredient("Scallions") == "green onion"
    assert next(item for item in pantry if item.normalized_name == "egg").unit == "count"


def test_marks_broad_ingredient_as_ambiguous() -> None:
    [cream] = parse_pantry("cream")
    assert cream.ambiguous is True
    assert cream.quantity is None
