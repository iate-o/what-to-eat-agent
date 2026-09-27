"""Streamlit interface for the Personal Food Decision Agent."""
from __future__ import annotations
import os
import streamlit as st
from dotenv import load_dotenv
from src.ingredient_matcher import match_ingredients
from src.llm_client import LLMClient,LLMError
from src.models import IngredientMatch,ShoppingList,UserConstraints
from src.orchestrator import WorkflowError,cook_from_pantry
from src.pantry import parse_pantry
from src.pantry_state import consume_recipe,pantry_to_text,update_inventory_text
from src.recipe_parser import parse_recipe_text
from src.shopping_list import build_shopping_list

load_dotenv()
st.set_page_config(page_title="Personal Food Decision Agent",page_icon="🥣",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""
<style>
:root { --ink:#17211b; --muted:#65716a; --lime:#d9ff57; --panel:#f4f7f1; --line:#dbe3d9; }
.stApp { background:linear-gradient(180deg,#fbfdf8 0%,#fff 42%); color:var(--ink); }
.block-container { max-width:1180px; padding-top:2rem; padding-bottom:4rem; }
h1,h2,h3 { color:var(--ink); letter-spacing:-.03em; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem; }
.eyebrow { display:inline-block; padding:.35rem .65rem; border-radius:999px; background:var(--lime); color:#243000; font-weight:750; font-size:.78rem; }
.lede { color:var(--muted); font-size:1.08rem; max-width:780px; }
.decision-step { padding:.65rem .8rem; border-left:3px solid #a8d900; background:var(--panel); margin:.3rem 0; border-radius:0 8px 8px 0; }
</style>
""",unsafe_allow_html=True)

def get_client(api_key,model):return LLMClient(api_key=api_key or None,model=model or None)
def split_values(text):return [v.strip() for v in text.split(",") if v.strip()]
def format_quantity(quantity,unit):
    if quantity is None:return "quantity not specified"
    clean=int(quantity) if quantity.is_integer() else round(quantity,2);return f"{clean} {unit or ''}".strip()
def match_label(match:IngredientMatch):
    if match.status=="partially_available":return f"{match.required_ingredient.name} - buy {format_quantity(match.quantity_missing,match.unit)} more"
    if match.status=="uncertain":return f"{match.required_ingredient.name} - {match.note or 'confirm pantry quantity'}"
    return f"{match.required_ingredient.name} - {format_quantity(match.quantity_required,match.unit)}"
def render_shopping_list(shopping:ShoppingList):
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("#### Already have")
        for m in shopping.available:st.markdown(f"✓ {m.required_ingredient.name}")
        if not shopping.available:st.caption("No confirmed matches")
    with c2:
        st.markdown("#### Check or top up")
        for m in [*shopping.partial,*shopping.uncertain]:st.markdown(f"• {match_label(m)}")
        if not shopping.partial and not shopping.uncertain:st.caption("Nothing to check")
    with c3:
        st.markdown("#### Need to buy")
        for i in shopping.to_buy:st.markdown(f"• **{i.ingredient}** - {format_quantity(i.quantity,i.unit)}")
        if not shopping.to_buy:st.success("Your pantry covers the recipe.")
def render_cook_result(result):
    best=result.best_match;st.markdown("## Best match");st.markdown(f"### {best.recipe.title}");st.write(best.recipe.description)
    cols=st.columns(5);cols[0].metric("Recipe score",f"{best.score.final_score:.0f}/100");cols[1].metric("Pantry used",f"{best.score.pantry_utilisation_rate:.0%}");cols[2].metric("Need to buy",best.score.missing_ingredient_count);cols[3].metric("Cooking time",f"{best.recipe.cooking_time_minutes} min");cols[4].metric("Serves",best.recipe.servings)
    st.markdown("### Pantry check");render_shopping_list(result.shopping_list)
    left,right=st.columns([1,1.1])
    with left:
        st.markdown("### Ingredients")
        for i in best.recipe.ingredients:st.markdown(f"- {format_quantity(i.quantity,i.unit)} **{i.name}**")
    with right:
        st.markdown("### Method")
        for n,step in enumerate(best.recipe.instructions,1):st.markdown(f"**{n}.** {step}")
    with st.expander("How the Agent Decided"):
        for n,step in enumerate(result.trace,1):st.markdown(f'<div class="decision-step"><strong>{n}</strong> &nbsp; {step}</div>',unsafe_allow_html=True)
        if result.rejected_candidates:
            st.markdown("#### Rejected candidates")
            for c in result.rejected_candidates:st.write(f"**{c.recipe.title}:** {', '.join(c.validation.issues)}")

with st.sidebar:
    st.markdown("### Model settings");api_key=st.text_input("OpenAI API key",value="",type="password",placeholder="Uses OPENAI_API_KEY if blank");model=st.text_input("Model",value=os.getenv("OPENAI_MODEL","gpt-4.1-mini"));st.caption("The key is not written by the app.")

st.markdown('<span class="eyebrow">Personal food decision agent</span>',unsafe_allow_html=True)
st.title("Decide what to cook with what you have.")
st.markdown('<p class="lede">Keep a session pantry, generate and validate recipe options, replan from feedback, and turn recipes into shopping actions.</p>',unsafe_allow_html=True)

if "pantry_text" not in st.session_state:st.session_state.pantry_text="300g chicken breast\n4 eggs\n200g spinach\nrice\nmushrooms"

pantry_tab,cook_tab,shopping_tab=st.tabs(["Pantry state","Cook from pantry","Recipe → shopping list"])
with pantry_tab:
    st.markdown("## Current pantry")
    edited=st.text_area("Inventory",value=st.session_state.pantry_text,height=230,key="pantry_editor")
    c1,c2=st.columns([1,1])
    with c1:
        if st.button("Save pantry",use_container_width=True):st.session_state.pantry_text=edited;st.success("Pantry state updated for this browser session.")
    with c2:
        additions=st.text_input("Add ingredients",placeholder="2 eggs, 300g tofu")
        if st.button("Add to pantry",use_container_width=True) and additions.strip():st.session_state.pantry_text=update_inventory_text(st.session_state.pantry_text,additions);st.rerun()
    st.caption("Session-only state: no account or cross-device persistence is claimed.")

with cook_tab:
    with st.form("cook_form"):
        left,right=st.columns([1.2,1])
        with left:pantry_text=st.text_area("Pantry used for this run",value=st.session_state.pantry_text,height=190)
        with right:
            c1,c2=st.columns(2);servings=c1.number_input("Servings",1,20,2);max_time=c2.slider("Maximum time",5,120,30,5,format="%d min")
            diets=st.multiselect("Dietary preference",["High protein","Calorie-conscious","Vegetarian","Vegan","Keto","Gluten-free","Dairy-free"]);allergies=st.text_input("Allergies",placeholder="Peanuts, shellfish");dislikes=st.text_input("Dislikes",placeholder="Mushrooms, chilli")
        find_recipes=st.form_submit_button("Find recipes",type="primary",use_container_width=True)
    if find_recipes:
        st.session_state.pantry_text=pantry_text
        constraints=UserConstraints(servings=int(servings),max_cooking_time_minutes=max_time,dietary_preferences=[d.lower() for d in diets],allergies=split_values(allergies),dislikes=split_values(dislikes))
        try:
            with st.spinner("Generating, validating and ranking candidates..."):result=cook_from_pantry(get_client(api_key,model),pantry_text,constraints)
            st.session_state.cook_result=result
        except (LLMError,WorkflowError) as exc:st.error(str(exc))
    if result:=st.session_state.get("cook_result"):
        render_cook_result(result)
        a,b=st.columns([1.3,1])
        with a:
            with st.form("feedback_form",clear_on_submit=True):
                feedback=st.text_input("What would you change?",placeholder="Under 20 minutes, no mushrooms, simpler...");replan=st.form_submit_button("Replan",use_container_width=True)
            if replan and feedback.strip():
                try:
                    updated=cook_from_pantry(get_client(api_key,model),st.session_state.pantry_text,result.constraints,feedback);st.session_state.cook_result=updated;st.rerun()
                except (LLMError,WorkflowError) as exc:st.error(str(exc))
        with b:
            if st.button("I cooked this - update pantry",type="primary",use_container_width=True):
                updated,warnings=consume_recipe(parse_pantry(st.session_state.pantry_text),result.best_match.recipe);st.session_state.pantry_text=pantry_to_text(updated)
                for warning in warnings:st.warning(warning)
                st.success("Known compatible ingredient quantities were deducted from the session pantry.")

with shopping_tab:
    with st.form("shopping_form"):
        left,right=st.columns(2)
        with left:shopping_pantry=st.text_area("Your pantry",value=st.session_state.pantry_text,height=250)
        with right:recipe_text=st.text_area("Paste a recipe",height=250,placeholder="Recipe title\n\nIngredients...\n\nMethod...")
        make_list=st.form_submit_button("Build shopping list",type="primary",use_container_width=True)
    if make_list:
        pantry=parse_pantry(shopping_pantry)
        if not pantry:st.error("Add at least one pantry ingredient.")
        elif not recipe_text.strip():st.error("Paste a recipe to analyse.")
        else:
            try:
                parsed=parse_recipe_text(get_client(api_key,model),recipe_text);shopping=build_shopping_list(match_ingredients(parsed.ingredients,pantry));st.session_state.shopping_result=(parsed,shopping)
            except LLMError as exc:st.error(str(exc))
    if shopping_result:=st.session_state.get("shopping_result"):
        parsed,shopping=shopping_result;st.markdown(f"## {parsed.title}");render_shopping_list(shopping)

st.divider();st.caption("Generated recipes are suggestions, not medical or nutritional advice. Verify allergy-sensitive ingredients and cooking safety.")
