"""Streamlit interface for the Personal Food Decision Agent."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from src.ingredient_matcher import match_ingredients
from src.llm_client import LLMClient, LLMError
from src.models import IngredientMatch, ShoppingList, UserConstraints
from src.orchestrator import WorkflowError, cook_from_pantry
from src.pantry import parse_pantry
from src.pantry_state import consume_recipe, pantry_to_text, update_inventory_text
from src.recipe_parser import parse_recipe_text
from src.shopping_list import build_shopping_list


load_dotenv()
st.set_page_config(
    page_title="Personal Food Decision Agent",
    page_icon="🥣",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --ink:#17211b; --muted:#65716a; --lime:#d9ff57; --panel:#f4f7f1; --line:#dbe3d9; }
    .stApp { background: linear-gradient(180deg, #fbfdf8 0%, #ffffff 42%); color: var(--ink); }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -0.035em; }
    h1 { font-size: clamp(2.25rem, 5vw, 4.4rem) !important; line-height: .98 !important; max-width: 820px; }
    [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem; box-shadow:0 8px 30px rgba(23,33,27,.05); }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    .eyebrow { display:inline-block; padding:.35rem .65rem; border-radius:999px; background:var(--lime); color:#243000; font-weight:750; font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; }
    .lede { color:var(--muted); font-size:1.1rem; max-width:780px; margin:.5rem 0 1.8rem; }
    .recipe-card { border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.25rem; background:#fff; margin:.6rem 0; }
    .recipe-card strong { font-size:1.08rem; }
    .tag { display:inline-block; background:var(--panel); border:1px solid var(--line); border-radius:999px; padding:.18rem .55rem; margin:.15rem .2rem .15rem 0; font-size:.78rem; }
    .decision-step { padding:.7rem .85rem; border-left:3px solid #a8d900; background:var(--panel); margin:.35rem 0; border-radius:0 8px 8px 0; }
    .stButton > button, .stFormSubmitButton > button { border-radius:10px; font-weight:700; }
    div[data-baseweb="tab-list"] { gap:1rem; }
    button[data-baseweb="tab"] { font-size:1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_client(api_key: str, model: str) -> LLMClient:
    return LLMClient(api_key=api_key or None, model=model or None)


def split_values(text: str) -> list[str]:
    return [value.strip() for value in text.split(",") if value.strip()]


def format_quantity(quantity: float | None, unit: str | None) -> str:
    if quantity is None:
        return "quantity not specified"
    clean = int(quantity) if quantity.is_integer() else round(quantity, 2)
    return f"{clean} {unit or ''}".strip()


def match_label(match: IngredientMatch) -> str:
    ingredient = match.required_ingredient.name
    if match.status == "partially_available":
        return f"{ingredient} — buy {format_quantity(match.quantity_missing, match.unit)} more"
    if match.status == "uncertain":
        return f"{ingredient} — {match.note or 'confirm pantry quantity'}"
    return f"{ingredient} — {format_quantity(match.quantity_required, match.unit)}"


def render_shopping_list(shopping: ShoppingList) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Already have")
        if shopping.available:
            for match in shopping.available:
                st.markdown(f"✓ {match.required_ingredient.name}")
        else:
            st.caption("No confirmed matches")
    with col2:
        st.markdown("#### Check or top up")
        if shopping.partial or shopping.uncertain:
            for match in [*shopping.partial, *shopping.uncertain]:
                st.markdown(f"• {match_label(match)}")
        else:
            st.caption("Nothing to check")
    with col3:
        st.markdown("#### Need to buy")
        if shopping.to_buy:
            for item in shopping.to_buy:
                st.markdown(
                    f"• **{item.ingredient}** — {format_quantity(item.quantity, item.unit)}"
                )
        else:
            st.success("Your pantry covers the recipe.")


def render_cook_result(result) -> None:
    best = result.best_match
    st.markdown("## Best match")
    st.markdown(f"### {best.recipe.title}")
    st.write(best.recipe.description)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Recipe score", f"{best.score.final_score:.0f}/100")
    metric_cols[1].metric("Pantry used", f"{best.score.pantry_utilisation_rate:.0%}")
    metric_cols[2].metric("Need to buy", best.score.missing_ingredient_count)
    metric_cols[3].metric("Cooking time", f"{best.recipe.cooking_time_minutes} min")
    metric_cols[4].metric("Serves", best.recipe.servings)

    if best.recipe.dietary_tags:
        st.markdown(
            "".join(f'<span class="tag">{tag}</span>' for tag in best.recipe.dietary_tags),
            unsafe_allow_html=True,
        )
    st.caption(best.score.explanation)

    st.markdown("### Pantry check")
    render_shopping_list(result.shopping_list)

    left, right = st.columns([1, 1.1])
    with left:
        st.markdown("### Ingredients")
        for ingredient in best.recipe.ingredients:
            optional = " · optional" if ingredient.optional else ""
            st.markdown(
                f"- {format_quantity(ingredient.quantity, ingredient.unit)} "
                f"**{ingredient.name}**{optional}"
            )
    with right:
        st.markdown("### Method")
        for number, step in enumerate(best.recipe.instructions, 1):
            st.markdown(f"**{number}.** {step}")

    if result.other_candidates:
        st.markdown("## Other candidates")
        cols = st.columns(min(2, len(result.other_candidates)))
        for index, candidate in enumerate(result.other_candidates):
            with cols[index % len(cols)]:
                st.markdown(
                    f"""<div class="recipe-card"><strong>{candidate.recipe.title}</strong><br>
                    <span style="color:#65716a">{candidate.recipe.cooking_time_minutes} min ·
                    {candidate.score.pantry_utilisation_rate:.0%} pantry use ·
                    score {candidate.score.final_score:.0f}</span><br><br>
                    {candidate.recipe.description}</div>""",
                    unsafe_allow_html=True,
                )

    with st.expander("How the Agent Decided"):
        for number, step in enumerate(result.trace, 1):
            st.markdown(
                f'<div class="decision-step"><strong>{number}</strong> &nbsp; {step}</div>',
                unsafe_allow_html=True,
            )
        if result.rejected_candidates:
            st.markdown("#### Rejected candidates")
            for candidate in result.rejected_candidates:
                st.write(f"**{candidate.recipe.title}:** {', '.join(candidate.validation.issues)}")


with st.sidebar:
    st.markdown("### Model settings")
    api_key = st.text_input(
        "OpenAI API key",
        value="",
        type="password",
        placeholder="Uses OPENAI_API_KEY if blank",
    )
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    st.caption("Keys entered here stay in this browser session and are not saved by the app.")


if "pantry_text" not in st.session_state:
    st.session_state.pantry_text = (
        "300g chicken breast\n4 eggs\n200g spinach\nrice\nmushrooms"
    )

st.markdown('<span class="eyebrow">Personal food decision agent</span>', unsafe_allow_html=True)
st.title("Decide what to cook with what you have.")
st.markdown(
    '<p class="lede">Keep a session pantry, generate and validate recipe options, '
    'replan from feedback, and turn recipes into shopping actions.</p>',
    unsafe_allow_html=True,
)

pantry_tab, cook_tab, shopping_tab = st.tabs(
    ["Pantry state", "Cook From My Pantry", "Recipe → Shopping List"]
)

with pantry_tab:
    st.markdown("## Current pantry")
    edited_pantry = st.text_area(
        "Inventory",
        value=st.session_state.pantry_text,
        height=230,
        key="pantry_editor",
    )
    save_col, add_col = st.columns(2)
    with save_col:
        if st.button("Save pantry", use_container_width=True):
            st.session_state.pantry_text = edited_pantry
            st.success("Pantry state updated for this browser session.")
    with add_col:
        additions = st.text_input("Add ingredients", placeholder="2 eggs, 300g tofu")
        if st.button("Add to pantry", use_container_width=True) and additions.strip():
            st.session_state.pantry_text = update_inventory_text(
                st.session_state.pantry_text,
                additions,
            )
            st.rerun()
    st.caption("Session-only state: no account or cross-device persistence is claimed.")


with cook_tab:
    with st.form("cook_form"):
        left, right = st.columns([1.2, 1])
        with left:
            pantry_text = st.text_area(
                "Pantry used for this run",
                value=st.session_state.pantry_text,
                height=190,
            )
        with right:
            c1, c2 = st.columns(2)
            servings = c1.number_input("Servings", min_value=1, max_value=20, value=2)
            max_time = c2.slider(
                "Maximum time",
                min_value=5,
                max_value=120,
                value=30,
                step=5,
                format="%d min",
            )
            diets = st.multiselect(
                "Dietary preference",
                [
                    "High protein",
                    "Calorie-conscious",
                    "Vegetarian",
                    "Vegan",
                    "Keto",
                    "Gluten-free",
                    "Dairy-free",
                ],
            )
            allergies = st.text_input("Allergies", placeholder="Peanuts, shellfish")
            dislikes = st.text_input("Dislikes", placeholder="Mushrooms, chilli")

        find_recipes = st.form_submit_button(
            "Find recipes",
            type="primary",
            use_container_width=True,
        )

    if find_recipes:
        st.session_state.pantry_text = pantry_text
        constraints = UserConstraints(
            servings=int(servings),
            max_cooking_time_minutes=max_time,
            dietary_preferences=[diet.lower() for diet in diets],
            allergies=split_values(allergies),
            dislikes=split_values(dislikes),
        )
        try:
            with st.spinner("Generating, validating, and ranking three candidates…"):
                client = get_client(api_key, model)
                result = cook_from_pantry(client, pantry_text, constraints)
            st.session_state.cook_result = result
        except (LLMError, WorkflowError) as exc:
            st.error(str(exc))

    if result := st.session_state.get("cook_result"):
        render_cook_result(result)

        feedback_col, inventory_col = st.columns([1.3, 1])
        with feedback_col:
            st.markdown("### What would you change?")
            with st.form("feedback_form", clear_on_submit=True):
                feedback = st.text_input(
                    "Feedback",
                    label_visibility="collapsed",
                    placeholder="Under 20 minutes, no mushrooms, vegetarian instead, fewer ingredients…",
                )
                replan = st.form_submit_button("Replan", use_container_width=True)

            if replan and feedback.strip():
                try:
                    with st.spinner("Updating constraints and replanning…"):
                        client = get_client(api_key, model)
                        updated = cook_from_pantry(
                            client,
                            st.session_state.pantry_text,
                            result.constraints,
                            feedback,
                        )
                    st.session_state.cook_result = updated
                    st.rerun()
                except (LLMError, WorkflowError) as exc:
                    st.error(str(exc))

        with inventory_col:
            st.markdown("### Finished cooking?")
            if st.button(
                "I cooked this — update pantry",
                type="primary",
                use_container_width=True,
            ):
                updated_pantry, warnings = consume_recipe(
                    parse_pantry(st.session_state.pantry_text),
                    result.best_match.recipe,
                )
                st.session_state.pantry_text = pantry_to_text(updated_pantry)
                for warning in warnings:
                    st.warning(warning)
                st.success(
                    "Known compatible ingredient quantities were deducted from the session pantry."
                )


with shopping_tab:
    with st.form("shopping_form"):
        left, right = st.columns(2)
        with left:
            shopping_pantry = st.text_area(
                "Your pantry",
                value=st.session_state.pantry_text,
                height=250,
            )
        with right:
            recipe_text = st.text_area(
                "Paste a recipe",
                height=250,
                placeholder="Recipe title\n\nIngredients…\n\nMethod…",
            )

        make_list = st.form_submit_button(
            "Build shopping list",
            type="primary",
            use_container_width=True,
        )

    if make_list:
        pantry = parse_pantry(shopping_pantry)
        if not pantry:
            st.error("Add at least one pantry ingredient.")
        elif not recipe_text.strip():
            st.error("Paste a recipe to analyse.")
        else:
            try:
                with st.spinner("Extracting ingredients and comparing your pantry…"):
                    client = get_client(api_key, model)
                    parsed = parse_recipe_text(client, recipe_text)
                    shopping = build_shopping_list(
                        match_ingredients(parsed.ingredients, pantry)
                    )
                st.session_state.shopping_result = (parsed, shopping)
            except LLMError as exc:
                st.error(str(exc))

    if shopping_result := st.session_state.get("shopping_result"):
        parsed, shopping = shopping_result
        st.markdown(f"## {parsed.title}")
        details = []
        if parsed.servings:
            details.append(f"Serves {parsed.servings}")
        if parsed.cooking_time_minutes:
            details.append(f"{parsed.cooking_time_minutes} min")
        if details:
            st.caption(" · ".join(details))

        if parsed.warnings:
            for warning in parsed.warnings:
                st.warning(warning)

        st.markdown("### Recognised ingredients")
        for ingredient in parsed.ingredients:
            st.markdown(
                f"- {format_quantity(ingredient.quantity, ingredient.unit)} "
                f"**{ingredient.name}**"
            )

        st.markdown("### Pantry-aware list")
        render_shopping_list(shopping)

        with st.expander("How the Agent Decided"):
            steps = [
                f"Parsed {len(parsed.ingredients)} recipe ingredients",
                f"Normalized {len(parse_pantry(shopping_pantry))} pantry items",
                "Matched names and compared compatible quantities deterministically",
                f"Marked {len(shopping.uncertain)} comparison(s) as uncertain",
                f"Created {len(shopping.to_buy)} shopping-list item(s)",
            ]
            for number, step in enumerate(steps, 1):
                st.markdown(
                    f'<div class="decision-step"><strong>{number}</strong> &nbsp; {step}</div>',
                    unsafe_allow_html=True,
                )

st.divider()
st.caption(
    "Recipes are generated suggestions, not medical or nutritional advice. "
    "Always verify allergy-sensitive ingredients and cooking safety."
)
