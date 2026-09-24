# Portfolio notes

Ground every claim in the current MVP. The strongest story is the product decision to separate generative planning from deterministic validation, not the size of the codebase.

## One-line resume version

Built a Streamlit AI pantry agent that generates structured recipe candidates, validates dietary and time constraints, ranks options deterministically, and creates quantity-aware shopping lists.

## Two-bullet resume version

- Designed and built a pantry-aware meal-planning MVP using Python, Streamlit, Pydantic structured outputs, and a single orchestrated generate → validate → rank → replan workflow.
- Created 15 unit tests and a 12-case offline evaluation suite covering constraint validation, ingredient utilisation, quantity matching, and shopping-list accuracy; achieved 100% validity and shopping exact match on the checked-in fixtures.

## Three-bullet resume version

- Framed and shipped an AI Recipe & Pantry Agent that reduces meal-planning friction by recommending recipes from available inventory and generating pantry-aware shopping lists.
- Split responsibilities between LLM generation/extraction and deterministic Python guardrails for allergies, diets, cooking time, unit comparison, scoring, and ranking.
- Built 15 tests and 12 offline evaluation cases; documented 100% fixture validity accuracy, 86.1% average pantry utilisation, and 100% shopping-list exact match while clearly separating these results from live-model quality.

## 30-second interview explanation

I built a pantry-aware meal-planning MVP, not a generic recipe chatbot. A user enters what they have and their constraints. The model generates structured recipe candidates, then deterministic Python checks allergies, diet, time, and completeness, ranks valid options, and compares the winner with pantry quantities to build a shopping list. If every candidate fails, the workflow retries once with the validation issues. I also built offline tests and evaluation fixtures so I could measure the deterministic layer separately from model variability.

## 90-second interview explanation

The user problem was decision friction: people have ingredients at home but still struggle to choose a meal that fits their time and dietary constraints. I designed two MVP journeys: recommend a meal from the pantry, and turn pasted recipe text into a pantry-aware shopping list.

The main product decision was not to let the LLM own the whole answer. It handles ambiguous tasks such as candidate generation, recipe extraction, and open-ended feedback. Pydantic converts those responses into typed objects. Deterministic functions then normalize ingredients, check explicit allergens and diet conflicts, enforce the cooking-time limit, compare compatible units, calculate pantry utilisation, and rank valid candidates with visible weights. The workflow can regenerate once when all candidates fail and can replan from user feedback, which is why I describe it as a narrow agentic workflow rather than an autonomous agent.

For quality, I added 15 unit tests and 12 offline fixtures. The current fixtures achieve 100% recipe-validity accuracy and shopping-list exact match, but I explicitly limit that claim to the small deterministic test set. The next evaluation step would be repeated live-model runs with model and prompt versions held constant.

## Interview questions

### Why AI?

Recipe generation, extraction from loosely formatted text, and qualitative feedback are language tasks with many acceptable outputs. An LLM handles that ambiguity well. It is not used for calculations or final ranking where normal code is easier to test and trust.

### Why an agent?

The implementation has a controlled loop: understand inputs, call a generation tool, inspect typed results, validate them, retry once after failure, rank valid options, call pantry-comparison tools, and replan after feedback. That supports the term "agentic workflow." It is intentionally one orchestrator, not a multi-agent system or a claim of broad autonomy.

### Why not a normal recipe search engine?

A search engine starts from indexed recipes and keywords. This MVP starts from household inventory plus multiple constraints, can generate a tailored candidate set, compares exact requirements with pantry quantities, and turns the result into a shopping action. A production version could combine this workflow with a verified recipe catalog, but search alone would not perform the complete decision process.

### What trade-offs did you make?

- I used a small alias dictionary instead of building an ingredient ontology.
- I compare only compatible mass, volume, and count units; density conversions stay uncertain.
- Pantry state is session-only, which keeps setup simple but prevents continuity across visits.
- The workflow retries once, limiting cost and latency at the expense of occasionally returning no recommendation.
- I used hand-authored offline fixtures before investing in a live-model evaluation harness.

### What would you improve next?

First, I would run repeated live-generation evaluations and analyze failures by constraint type. After validating the core journeys with users, I would add persistent pantry state and expiry-aware prioritisation. Verified nutrition data, weekly planning, and grocery integrations would come later because they add external dependencies and broader product risk.

### How did you evaluate quality?

I separated deterministic correctness from model quality. Fifteen unit tests cover normalization, aliases, quantity handling, validation, ranking, deduplication, and retry behavior. Twelve fixed cases report validity accuracy, pantry utilisation, constraint compliance, missing ingredient count, shopping precision/recall, and exact match. The current 100% results apply only to those fixtures; live LLM quality is not yet benchmarked.

### What did you learn from building it?

The main lesson was that reliable AI product behavior often comes from the boundary around the model. Typed outputs make generation inspectable, deterministic checks make policies testable, and an explicit uncertain state prevents false precision. I also learned to be precise about the word "agent": a small observable workflow with validation and replanning can be agentic without needing a large orchestration framework.
