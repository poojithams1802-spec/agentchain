# Phase 3 Ablation Summary

Source artifact: `results\phase3_ablation_gemini_20261011.json`

> These results reflect the saved experiments. Metrics are not evidence of an LLM improvement when fallback was used.

| Config | Method | Status | Tests | Accuracy* | LLM calls | Fallback |
|---|---|---|---:|---:|---:|---|
| A | LLM only | budget_exhausted | 3 | N/A | 3 | True |
| B | LLM + RAG | budget_exhausted | 3 | N/A | 3 | True |
| C | LLM + chain context | budget_exhausted | 3 | N/A | 3 | True |
| D | LLM + RAG + chain context | budget_exhausted | 3 | N/A | 3 | True |

*Accuracy measures agreement with the configured expected sequence; it does not independently establish test correctness.

## Interpretation

- Compare configurations only under equivalent starting state, budget, candidate pool, and evaluation procedure.
- Fallback usage means results cannot, by themselves, establish improved LLM reasoning.
- Missing chain-validation or mitigation metrics must remain unreported rather than being inferred.
