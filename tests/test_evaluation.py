from src.evaluation import classify_validation_failures,summarise_failure_taxonomy
from src.models import ValidationResult
def test_failure_taxonomy_maps_validation_issues():
    v=ValidationResult(valid=False,allergy_safe=False,diet_compliant=True,within_time_limit=False,structurally_valid=True,pantry_feasible=True,issues=["Contains allergy conflict: peanut","Cooking time (45 min) exceeds or omits the 30-minute limit"]);assert classify_validation_failures(v)==["allergy_conflict","time_limit"] and summarise_failure_taxonomy([v])=={"allergy_conflict":1,"time_limit":1}
