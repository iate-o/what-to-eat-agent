# Prompt and workflow experiments

Run the fixed suite and a reviewed live-generation sample before recording a result. Never mix model versions within one row.

| Version | Model | Change | Constraint compliance | Avg pantry utilisation | Shopping accuracy | Notes |
|---|---|---|---:|---:|---:|---|
| v1 | — | Baseline: generate three → validate → rank | — | — | — | Populate after first controlled run |
| v2 | — |  | — | — | — |  |

## Run notes

- Record the date, model snapshot, prompt commit, temperature/settings, and case count.
- Review allergy failures individually; a high average must never hide a hard-constraint failure.
- Keep offline deterministic metrics separate from live generation metrics.
