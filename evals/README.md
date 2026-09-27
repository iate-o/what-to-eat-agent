# Evaluation

The fixed suite evaluates deterministic product behavior separately from live model quality. It covers recipe validity, pantry utilisation, constraint compliance, missing ingredients, shopping-list accuracy, and a stable failure taxonomy.

Run:

```bash
python -m evals.run_evals
```

The checked-in fixture metrics are portfolio evidence for the deterministic layer only. They are not production or live-model benchmarks.

Current fixture metrics:

- Recipe validity accuracy: 100%
- Average pantry utilisation: 86.1%
- Average constraint compliance: 86.1%
- Average missing ingredient count: 0.44
- Shopping precision / recall / exact match: 100% / 100% / 100%

Failure taxonomy is reported separately so aggregate accuracy does not hide allergy, diet, time, structure, dislike, or pantry-feasibility failures.
