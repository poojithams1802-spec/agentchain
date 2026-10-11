# Phase 3 Ablation Evaluation

Source: `phase3_ablation_gemini_20261011.json`

All configurations present: **True**
Performance comparison valid: **False**

| Config | Status | Tests | LLM calls | Fallbacks | Accuracy (reported) | Eligible |
|---|---|---:|---:|---:|---:|---|
| A — llm_only | budget_exhausted | 1/3 | 2 | 0 | 0.3333 | No |
| B — llm_rag | completed | 3/3 | 3 | 2 | 1.0 | No |
| C — llm_chain | completed | 3/3 | 3 | 3 | 1.0 | No |
| D — llm_rag_chain | completed | 3/3 | 3 | 3 | 1.0 | No |

## Interpretation

- A completed run is not automatically a valid comparison.
- Fallback decisions are reported separately from LLM calls.
- Reported selection accuracy is not independently validated.
- Do not claim RAG or chain-context improvements from ineligible runs.
