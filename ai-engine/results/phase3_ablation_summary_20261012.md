# Phase 3 Ablation Summary

Source artifact: `results\phase3_ablation_gemini_20261011.json`

> These results reflect the saved experiments. They do not establish an LLM improvement when fallback is used or when comparisons are invalid.

| Config | Method                    | Status           | Tests requested | Tests selected | Source selection accuracy | LLM calls | Fallback used | Fallback decisions |
| ------ | ------------------------- | ---------------- | --------------: | -------------: | ------------------------- | --------: | ------------- | -----------------: |
| A      | LLM only                  | budget_exhausted |               3 |              1 | Not available             |         2 | false         |                  0 |
| B      | LLM + RAG                 | completed        |               3 |              3 | Not available             |         3 | true          |                  3 |
| C      | LLM + chain context       | completed        |               3 |              3 | Not available             |         3 | true          |                  3 |
| D      | LLM + RAG + chain context | budget_exhausted |               3 |              1 | Not available             |         2 | false         |                  0 |

## Interpretation

- All configurations used the same initial state, but their actual execution outcomes and available budgets differed.
- Configurations B and C used fallback for every decision.
- Configurations A and D exhausted their time budgets after selecting one test.
- `selection_accuracy` is null in the source JSON; do not infer or substitute an accuracy value.
- The evaluation artifact marks the performance comparison invalid. No configuration can be declared superior from these results.
- Missing chain-validation and mitigation metrics must remain unreported rather than inferred.
- A successful LLM-backed ablation remains pending.
