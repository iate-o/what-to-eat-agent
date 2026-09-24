"""Typed contracts shared by the agent workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PantryItem(BaseModel):
    name: str
    normalized_name: str
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    ambiguous: bool = False


class UserConstraints(BaseModel):
    servings: int = Field(default=2, ge=1, le=20)
    max_cooking_time_minutes: int = Field(default=30, ge=5, le=240)
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    notes: str | None = None


class RecipeIngredient(BaseModel):
    name: str
    normalized_name: str = ""
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    optional: bool = False


class RecipeCandidate(BaseModel):
    title: str
    description: str = ""
    servings: int = Field(default=2, ge=1)
    cooking_time_minutes: int = Field(default=0, ge=0)
    ingredients: list[RecipeIngredient]
    instructions: list[str]
    dietary_tags: list[str] = Field(default_factory=list)
    substitutions: list[str] = Field(default_factory=list)


class RecipeCandidateBatch(BaseModel):
    recipes: list[RecipeCandidate]


class ParsedRecipe(BaseModel):
    title: str = "Untitled recipe"
    servings: int | None = Field(default=None, ge=1)
    cooking_time_minutes: int | None = Field(default=None, ge=0)
    ingredients: list[RecipeIngredient]
    instructions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    valid: bool
    allergy_safe: bool
    diet_compliant: bool
    within_time_limit: bool
    structurally_valid: bool
    pantry_feasible: bool
    issues: list[str] = Field(default_factory=list)


class RecipeScore(BaseModel):
    pantry_utilisation_rate: float = Field(ge=0, le=1)
    missing_ingredient_count: int = Field(ge=0)
    constraint_compliance: float = Field(ge=0, le=1)
    cooking_time_fit: float = Field(ge=0, le=1)
    estimated_complexity: Literal["low", "medium", "high"]
    final_score: float = Field(ge=0, le=100)
    explanation: str


MatchStatus = Literal["available", "partially_available", "missing", "uncertain"]


class IngredientMatch(BaseModel):
    required_ingredient: RecipeIngredient
    pantry_match: PantryItem | None = None
    status: MatchStatus
    quantity_required: float | None = None
    quantity_available: float | None = None
    quantity_missing: float | None = None
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)
    note: str | None = None


class ShoppingListItem(BaseModel):
    ingredient: str
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    reason: str


class ShoppingList(BaseModel):
    available: list[IngredientMatch] = Field(default_factory=list)
    partial: list[IngredientMatch] = Field(default_factory=list)
    missing: list[IngredientMatch] = Field(default_factory=list)
    uncertain: list[IngredientMatch] = Field(default_factory=list)
    to_buy: list[ShoppingListItem] = Field(default_factory=list)


class ScoredRecipe(BaseModel):
    recipe: RecipeCandidate
    validation: ValidationResult
    score: RecipeScore
    matches: list[IngredientMatch]


class CookResult(BaseModel):
    best_match: ScoredRecipe
    other_candidates: list[ScoredRecipe] = Field(default_factory=list)
    rejected_candidates: list[ScoredRecipe] = Field(default_factory=list)
    shopping_list: ShoppingList
    constraints: UserConstraints
    pantry: list[PantryItem]
    trace: list[str]


class FeedbackUpdate(BaseModel):
    max_cooking_time_minutes: int | None = Field(default=None, ge=5, le=240)
    dietary_preferences: list[str] | None = None
    add_allergies: list[str] = Field(default_factory=list)
    add_dislikes: list[str] = Field(default_factory=list)
    notes: str | None = None
