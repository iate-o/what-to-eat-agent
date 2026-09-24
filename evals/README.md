# Evaluation

The fixed suite checks deterministic product behavior without making API calls. It covers normal and constrained recommendations, hard allergy checks, diet conflicts, short time limits, sparse pantries, ingredient aliases, partial quantities, and uncertain matches.

Run from the repository root:

```bash
python -m evals.run_evals
```

The output reports recipe-validity accuracy, average pantry utilisation, average constraint compliance, average missing-ingredient count, shopping-list precision, recall, and exact match. The recommendation fixtures represent candidate outputs; this isolates the validator, matcher, and scorer from model variability. Evaluate live generation separately against the same cases when changing models or prompts.

Current checked-in results:

| Metric | Result |
|---|---:|
| Recipe validity accuracy | 100% |
| Average pantry utilisation | 86.1% |
| Average constraint compliance | 86.1% |
| Average missing ingredient count | 0.44 |
| Shopping precision / recall / exact match | 100% / 100% / 100% |

These are results for 12 hand-authored offline fixtures, not production or live-model benchmarks.

User satisfaction is deliberately reported as unmeasured. Collect thumbs-up/down and qualitative feedback from real sessions before adding it as a benchmark.
