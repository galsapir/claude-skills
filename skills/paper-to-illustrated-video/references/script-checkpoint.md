# Script checkpoint

Send this before rendering anything. Iterate on text here; it is cheap. Iterating after a render
costs a full re-render and a re-review.

## Beat table template

| time | motion | on-screen text |
|---|---|---|
| 0-2 s | opening card | paper or benchmark name, one small word under it ("illustrated") |
| 2-9 s | orient: the object of study assembles (cohort, dataset, system) | one title, counters with accurate granularity, a one-line note if a counter could mislead |
| 9-17 s | mechanism: how the paper turns the object into comparable evidence | a card with 3-5 fixed fields; cycle 2-3 real examples from different families |
| 17-24 s | result 1, its own scene | header (eyebrow, title, scope line), data annotations, no slogan |
| 24-29 s | result 2, its own scene, drawn live (axes, points, intervals, frontier) | header with scope tag ("n models · n tasks · validation split") |
| 29-31 s | takeaway replaces the header; wordmark fades in; hold | the paper's own sentence for the finding; name only, no URL unless asked |

Rules the table must satisfy:

- Every number on screen has a source table or a claim-check row.
- Every result has its own scene. No visual doubles as evidence for two findings.
- Counters match what is drawn (cards = domains, not tasks) and say so.
- Text density: one line a viewer must read per ~2 s. Data scenes hold 5-8 s.
- Final frame works as a still.

## Questions to ask at the checkpoint

1. Duration budget, and whether it may stretch for comprehension.
2. Case: sentence case (matches most figures) or the author's lowercase chat voice.
3. Which visual carries each result (per-task strip vs per-category heatmap, etc.).
4. URL or logo in the video: default none if the post carries the link.
5. How many worked examples; one example often reads as "this is all we do".
6. Anything the paper requires to be labelled wherever it appears (validation split, synthetic).

## Voice: what got rejected and why

From the PhenoBench announcement video (2026-09-05), the author rejected:

- "Now the answers are comparable." ("the linkediniest line ever written, this isn't a movie trailer")
- "A model that wins one task can lose the next." (misstated the finding; the jagged frontier is
  about being strong on some task types and weak on others, not per-task wins and losses)
- A slogan-like end subline.
- "led classification, not the other three" ("not x but y" construction). Accepted form:
  "led classification, behind on other task types".

Accepted lines, for calibration:

- "HPP longitudinal cohort" · "15 clinical domains" · "90 tasks" · "one card per domain; each domain groups several tasks"
- "Each task fixes the target, the eligible population, the timing, the split, and the metric."
- "Methods are scored on the same held-out participants."
- "Win rate within each task type" · "14 LLMs · 40 tasks · pairwise against other LLMs on the same task"
- "GPT-5.4 nano: better at follow-up forecasting than phenotype recovery"
- "Cost did not predict performance on the 11 shared tasks."

## Worked example: PhenoBench (31 s)

| time | scene | evidence source |
|---|---|---|
| 0.0-2.2 | opening card | none |
| 1.9-9.4 | body silhouette from Figure 1A, 15 domain cards, counters 15 / 90 | Figure 1A crops; abstract counts |
| 9.1-17.4 | example-task card cycling HbA1c (R²), gut microbiome identity retrieval (Recall@1), diet-to-sleep causal effect (ATE, bpm) | task cards in the benchmark repository |
| 17.1-23.8 | within-category pairwise win-rate heatmap, colour only, numbers on leader and two called-out rows, legend | `task_rows.csv`, same computation as the manuscript figure |
| 23.5-31.0 | cost vs win rate, points cheapest first, CIs, Pareto frontier drawn live; takeaway; wordmark | `win_rates_common.csv`, `cost_failures.csv` |
