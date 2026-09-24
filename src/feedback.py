"""Translate qualitative feedback into a small, explicit constraint update."""

from __future__ import annotations

import re

from .llm_client import LLMClient, load_prompt
from .models import FeedbackUpdate, UserConstraints


KNOWN_DIETS = ("vegetarian", "vegan", "keto", "gluten-free", "dairy-free", "high protein")


def _deterministic_feedback(text: str) -> FeedbackUpdate:
    lowered = text.lower().strip()
    update = FeedbackUpdate()
    time_match = re.search(r"(?:under|within|max(?:imum)?(?: of)?)\s*(\d+)\s*(?:minutes?|mins?)", lowered)
    if time_match:
        update.max_cooking_time_minutes = int(time_match.group(1))
    elif "faster" in lowered or "quicker" in lowered:
        update.max_cooking_time_minutes = 20

    selected_diets = [diet for diet in KNOWN_DIETS if diet in lowered]
    if selected_diets:
        update.dietary_preferences = selected_diets
    elif "lighter" in lowered or "lower calorie" in lowered:
        update.dietary_preferences = ["calorie-conscious"]

    no_match = re.search(r"(?:no|without|don't want|do not want)\s+([a-z][a-z -]{1,30})", lowered)
    if no_match:
        dislike = re.split(r"[,.;]|\s+(?:and|but)\s+", no_match.group(1))[0].strip()
        if dislike:
            update.add_dislikes = [dislike]

    if "less spicy" in lowered or "not spicy" in lowered:
        update.notes = "Keep spice mild."
    elif "fewer ingredients" in lowered or "too complicated" in lowered:
        update.notes = "Prefer fewer ingredients and simpler steps."
    return update


def interpret_feedback(client: LLMClient | None, text: str) -> FeedbackUpdate:
    update = _deterministic_feedback(text)
    if any(
        (
            update.max_cooking_time_minutes,
            update.dietary_preferences,
            update.add_dislikes,
            update.notes,
        )
    ):
        return update
    if client is None:
        return FeedbackUpdate(notes=text.strip())
    return client.parse(load_prompt("interpret_feedback.txt", feedback=text), FeedbackUpdate)


def apply_feedback(constraints: UserConstraints, update: FeedbackUpdate) -> UserConstraints:
    data = constraints.model_dump()
    if update.max_cooking_time_minutes is not None:
        data["max_cooking_time_minutes"] = update.max_cooking_time_minutes
    if update.dietary_preferences is not None:
        data["dietary_preferences"] = update.dietary_preferences
    data["allergies"] = list(dict.fromkeys([*data["allergies"], *update.add_allergies]))
    data["dislikes"] = list(dict.fromkeys([*data["dislikes"], *update.add_dislikes]))
    if update.notes:
        data["notes"] = " ".join(filter(None, [data.get("notes"), update.notes]))
    return UserConstraints.model_validate(data)
