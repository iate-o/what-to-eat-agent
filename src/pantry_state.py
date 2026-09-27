"""Session-level pantry state and deterministic inventory updates."""
from __future__ import annotations
from .models import PantryItem,RecipeCandidate
from .pantry import normalize_unit,parse_pantry
CONVERSIONS={"g":("mass",1.0),"kg":("mass",1000.0),"ml":("volume",1.0),"l":("volume",1000.0),"tsp":("volume",5.0),"tbsp":("volume",15.0),"cup":("volume",250.0),"count":("count",1.0)}
def _base(quantity,unit):
    unit=normalize_unit(unit);c=CONVERSIONS.get(unit or "")
    if not c:return None
    return c[0],quantity*c[1]
def merge_pantry(existing,incoming):
    merged={(i.normalized_name,normalize_unit(i.unit)):i.model_copy(deep=True) for i in existing}
    for item in incoming:
        key=(item.normalized_name,normalize_unit(item.unit));current=merged.get(key)
        if current is None:merged[key]=item.model_copy(deep=True)
        elif current.quantity is not None and item.quantity is not None:current.quantity+=item.quantity
        elif item.quantity is not None:current.quantity=item.quantity
    return list(merged.values())
def pantry_to_text(items):
    lines=[]
    for item in items:
        if item.quantity is None:lines.append(item.name);continue
        qty=int(item.quantity) if item.quantity.is_integer() else round(item.quantity,2);lines.append(f"{qty}{item.unit or ''} {item.name}".strip())
    return "\n".join(lines)
def consume_recipe(pantry,recipe):
    updated=[i.model_copy(deep=True) for i in pantry];warnings=[]
    for ingredient in recipe.ingredients:
        if ingredient.optional:continue
        match=next((i for i in updated if i.normalized_name==ingredient.normalized_name),None)
        if match is None:continue
        if ingredient.quantity is None or match.quantity is None:warnings.append(f"Could not deduct {ingredient.name}: quantity is unknown.");continue
        req=_base(ingredient.quantity,ingredient.unit);avail=_base(match.quantity,match.unit)
        if not req or not avail or req[0]!=avail[0]:warnings.append(f"Could not deduct {ingredient.name}: units are not safely comparable.");continue
        unit=normalize_unit(match.unit)
        if unit not in CONVERSIONS:continue
        remaining=max(0.0,avail[1]-req[1]);match.quantity=round(remaining/CONVERSIONS[unit][1],3)
    return [i for i in updated if i.quantity is None or i.quantity>0],warnings
def update_inventory_text(current_text,added_text=""):
    return pantry_to_text(merge_pantry(parse_pantry(current_text),parse_pantry(added_text)))
