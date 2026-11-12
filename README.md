# Batch Before Cache — artifact

Derived data and a reproduction script for the paper *Batch Before Cache: A Per-Call Audit of Where the Money Went in Ten LLM Evaluation Campaigns*.

## Contents

| File | What it is |
|---|---|
| `per_call.csv` | One row per API call (66,737 rows). No prompts or outputs. |
| `price_sheet.json` | The single dated price sheet (USD per million tokens) used to re-price every call; batch calls at 0.5×. |
| `sensitivity_cache_gap.csv` | Cache-gap results for the 16-cell sensitivity grid (lifetime × window × minimum prefix), Table V. |
| `fig1_spend_split.json` | Data behind Fig. 1. |
| `reproduce.py` | Regenerates the campaign table, the model table, the generation comparison, the per-call ledger check and the headline shares. Python 3, standard library only. |

## Run

```
python3 reproduce.py
```

Expected headline line: total $285.37 over 66,737 calls; gates 2.9%; rework 4.6%; cache gap $5.67 (2.0%); batch-eligible $63.56 (22.3%); cache ceiling $41.78 (14.6%); interactive $100.59; output tokens 74.0% of priced spend.

## Columns of `per_call.csv`

- `campaign` C1–C10, `generation` G1 (hand-built) / G2 (one-shot cloud) / G3 (template harness)
- `model`, `vendor` (Anthropic, OpenAI, Groq). Two campaigns logged short model labels (`haiku`, `sonnet`); four failed calls carry no model; `stub-router-1` is a zero-cost stub.
- `phase`: gate (canary/pilot), prod, aborted, failed; `ok`, `retry`, `parse_ok` (blank when the campaign did not parse output)
- `batch` (sent through a batch API), `interactive` (call depended on the previous reply, so not batch-eligible)
- `input_uncached`, `cache_read`, `cache_write`, `output`: token counts; `tokens_logged` = 0 where the campaign logged cost but not tokens
- `cost_sheet_usd`: cost under `price_sheet.json`; `cost_logged_usd`: cost the harness itself recorded (blank if none)
- `ach_cache_tokens`: achievable cached-prefix tokens under the default setting (5-minute lifetime, window 40, documented minimum); blank for campaigns without request text

## Not included

The raw exchange logs contain material from studies still under review and are not released. The prefix search behind the cache gap (Algorithm 1) needs request text, so its results are shipped as computed in `ach_cache_tokens` and `sensitivity_cache_gap.csv`. One campaign's ledger discrepancy (C8) is a campaign-level comparison with no per-call logged cost, so it does not appear in the per-call ledger check.
