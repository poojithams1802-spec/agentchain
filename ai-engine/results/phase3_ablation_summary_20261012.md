# Phase 3 Ablation Summary

Source artifact: `results\phase3_ablation_gemini_20261011.json`

> These results reflect the saved experiments. Metrics are not evidence of an LLM improvement when fallback was used.

| Config | Method | Status | Tests requested | Tests selected | Reported selection accuracy* | LLM calls | Fallback used | Fallback decisions |
|---|---|---|---:|---:|---:|---:|---|---:|
| A | LLM only | budget_exhausted | 3 | 1 | 0.3333 | 2 | false | 0 |
| B | LLM + RAG | completed | 3 | 3 | 1.0 | 3 | true | 2 |
| C | LLM + chain context | completed | 3 | 3 | 1.0 | 3 | true | 3 |
| D | LLM + RAG + chain context | completed | 3 | 3 | 1.0 | 3 | true | 3 |

*Reported selection accuracy is not independently validated as test correctness (`accuracy_independently_validated: false`). The evaluation artifact marks the performance comparison invalid (`performance_comparison_valid: false`); these values do not establish that any configuration is superior.

## Interpretation

- Compare configurations only under equivalent starting state, budget, candidate pool, and evaluation procedure.
- Fallback usage means results cannot, by themselves, establish improved LLM reasoning.
- Missing chain-validation or mitigation metrics must remain unreported rather than being inferred.
