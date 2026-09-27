from src.feedback import apply_feedback,interpret_feedback
from src.models import UserConstraints
def test_feedback_updates_time_and_dislike_without_model():
    update=interpret_feedback(None,"under 20 minutes and no mushrooms");c=apply_feedback(UserConstraints(),update);assert c.max_cooking_time_minutes==20 and "mushrooms" in c.dislikes
def test_feedback_can_switch_diet():
    c=apply_feedback(UserConstraints(),interpret_feedback(None,"vegetarian instead"));assert c.dietary_preferences==["vegetarian"]
