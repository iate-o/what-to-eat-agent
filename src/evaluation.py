"""Stable failure taxonomy for product-quality analysis."""
from collections import Counter
FAILURE_LABELS=("allergy_conflict","diet_conflict","dislike_conflict","time_limit","structure","pantry_feasibility","other")
def classify_validation_failures(validation):
    labels=[]
    for issue in validation.issues:
        lowered=issue.lower()
        if "allergy conflict" in lowered:labels.append("allergy_conflict")
        elif "disliked ingredient" in lowered:labels.append("dislike_conflict")
        elif "conflicts with" in lowered or "high-protein" in lowered:labels.append("diet_conflict")
        elif "cooking time" in lowered:labels.append("time_limit")
        elif "missing a title" in lowered or "usable instructions" in lowered:labels.append("structure")
        elif "too many ingredients" in lowered:labels.append("pantry_feasibility")
        else:labels.append("other")
    return list(dict.fromkeys(labels))
def summarise_failure_taxonomy(results):
    c=Counter()
    for r in results:c.update(classify_validation_failures(r))
    return {label:c[label] for label in FAILURE_LABELS if c[label]}
