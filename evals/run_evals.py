"""Run the fixed offline evaluation without an API key."""
from __future__ import annotations
import json
from pathlib import Path
from src.evaluation import summarise_failure_taxonomy
from src.ingredient_matcher import match_ingredients
from src.models import RecipeCandidate,RecipeIngredient,UserConstraints
from src.pantry import normalize_ingredient,parse_pantry
from src.scorer import score_recipe
from src.shopping_list import build_shopping_list
from src.validator import validate_recipe
def safe_ratio(n,d):return n/d if d else 1.0
def main():
    cases=json.loads((Path(__file__).parent/"test_cases.json").read_text());validity_correct=0;recommendation_count=0;util=[];comp=[];missing=[];shopping_precision=[];shopping_recall=[];shopping_exact=[];results=[];validations=[]
    for case in cases:
        pantry=parse_pantry(case["pantry"])
        if case["type"]=="recommendation":
            recommendation_count+=1;constraints=UserConstraints.model_validate(case["constraints"]);recipe=RecipeCandidate.model_validate(case["recipe"])
            for ingredient in recipe.ingredients:ingredient.normalized_name=normalize_ingredient(ingredient.normalized_name or ingredient.name)
            validation=validate_recipe(recipe,constraints,pantry);validations.append(validation);score=score_recipe(recipe,validation,pantry,constraints);correct=validation.valid==case["expected_valid"];validity_correct+=int(correct);util.append(score.pantry_utilisation_rate);comp.append(score.constraint_compliance);missing.append(score.missing_ingredient_count);results.append({"id":case["id"],"valid":validation.valid,"expected_valid":case["expected_valid"],"correct":correct,"constraint_compliance":score.constraint_compliance,"pantry_utilisation":score.pantry_utilisation_rate,"missing_ingredients":score.missing_ingredient_count,"failures":validation.issues})
        else:
            ingredients=[RecipeIngredient.model_validate(i) for i in case["ingredients"]];shopping=build_shopping_list(match_ingredients(ingredients,pantry));predicted={i.ingredient for i in shopping.to_buy};expected=set(case["expected_missing"]);tp=len(predicted&expected);precision=safe_ratio(tp,len(predicted));recall=safe_ratio(tp,len(expected));exact=predicted==expected;shopping_precision.append(precision);shopping_recall.append(recall);shopping_exact.append(exact);results.append({"id":case["id"],"predicted_missing":sorted(predicted),"expected_missing":sorted(expected),"precision":precision,"recall":recall,"exact_match":exact,"uncertain_matches":len(shopping.uncertain)})
    summary={"cases":len(cases),"recipe_validity_accuracy":safe_ratio(validity_correct,recommendation_count),"average_pantry_utilisation":sum(util)/len(util),"average_constraint_compliance":sum(comp)/len(comp),"average_missing_ingredient_count":sum(missing)/len(missing),"shopping_precision":sum(shopping_precision)/len(shopping_precision),"shopping_recall":sum(shopping_recall)/len(shopping_recall),"shopping_exact_match":sum(shopping_exact)/len(shopping_exact),"failure_taxonomy":summarise_failure_taxonomy(validations),"user_satisfaction":"Not measured; requires real user feedback"}
    print(json.dumps({"summary":summary,"results":results},indent=2))
if __name__=="__main__":main()
