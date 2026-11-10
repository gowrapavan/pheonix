# PHOENIX: Benchmark Protocol

Status: Draft v0.1. Decisions below are made **before** results exist, to avoid tuning the evaluation to the system.

## Research question

Can a hybrid deterministic and AI-assisted system repair website extraction failures while keeping the rate of incorrectly accepted repairs low?

## Unit of evaluation

One **case** = (fixture, mutation set, seed), with a manifest from `MUTATION_HARNESS.md` giving the expected decision and expected output.

## Splits

Split by **fixture/site template**, not by random case. Random splitting leaks: the same site with a different class rename would appear in both train and test.

| Split | Share | Use |
|---|---|---|
| Development | ~60% | Build and tune freely |
| Validation | ~20% | Compare variants, set thresholds, calibrate confidence |
| **Held-out test** | ~20% | Never used for tuning; run only at milestones |

Rules:
- Assign fixtures to splits once, by a fixed hash of the fixture ID, and commit the assignment file.
- Every run on the test split is logged (date, commit hash, config). If any change is made *because of* a test result, that test split is contaminated: record it and create a fresh test split.
- Report the number of test-split runs alongside results.

## Systems compared

| ID | System | Purpose |
|---|---|---|
| B0 | Traditional scraper, no repair | Lower bound |
| B1 | Selector fallback only (ordered alternative selectors) | Cheap deterministic baseline |
| B2 | LLM-only repair, applied if output passes schema | The naive "AI scraper" approach |
| P | PHOENIX full pipeline (tiers + validation + confidence gate) | System under test |

Ablations of P (run on validation): without held-out validation, without confidence gate, deterministic tier only, LLM tier only.

## Outcome labels per case

| Label | Meaning |
|---|---|
| `correct_accept` | Repair accepted, output matches ground truth |
| **`false_accept`** | Repair accepted, output is wrong |
| `correct_reject` | Rejected or escalated, and no correct repair was possible or safe |
| `missed_repair` | Rejected or escalated though a correct repair existed |
| `correct_no_action` | No-op case, left untouched |
| `unnecessary_repair` | Changed the spec on a no-op case |
| `correct_blocked` / `missed_block` | Block page classified correctly / not |
| `review` | Sent to human; scored separately, not counted as accept |

## Metrics

**Primary:**
- **False-accept rate (FAR)** = `false_accept / all accepted repairs`.
- **FAR over all recoverable and unrecoverable cases** = `false_accept / all cases`, which keeps a system from looking safe by accepting almost nothing.

**Secondary:**
- Correct recovery rate = `correct_accept / recoverable cases`.
- Review rate and missed-repair rate (cost of caution).
- Unnecessary-repair rate on M13 no-ops.
- Block misclassification rate on M14.
- Per-mutation breakdown (which mutation types fail).
- Cost per case: wall time, LLM tokens, LLM calls.
- Confidence calibration: reliability curve and expected calibration error on the validation split.

Always report recovery rate **and** FAR together. Neither alone is meaningful.

## Statistics

- Run LLM-dependent systems with multiple seeds (suggested: 3+), temperature 0, and report variability.
- Report 95% confidence intervals (Wilson interval for proportions).
- Report absolute counts next to every percentage (e.g. "2 of 214 accepts").
- With small test sets, say so plainly; do not present sub-1% differences as meaningful.

## Pre-registered hypotheses (edit before first run, not after)

- H1: P has a lower FAR than B2 at comparable recovery rate.
- H2: P recovers more correct cases than B0 and B1.
- H3: Removing held-out validation raises FAR.
- H4: The LLM tier adds recovery on compound mutations but at higher cost.

Any hypothesis may be false. A negative result is reported the same as a positive one.

## Targets (to revisit after the first baseline)

These are goals, not claims: FAR on the order of 1% or lower on the held-out test; most routine mutations (M01-M08, M10) recovered without a human; M09, M12, M14 never silently accepted.

## Reproducibility requirements

- One command: `python scripts/run_benchmark.py --split test --system P`.
- Pinned dependencies and Python version; commit hash recorded in every report.
- Frozen fixtures with SHA-256 checks.
- LLM calls cached by (provider, model version, prompt hash) so reruns don't depend on live API state; log exact model IDs.
- Results written as machine-readable JSON plus a generated HTML report.
- Failed and false-accept cases published with their manifests, not only aggregates.

## Threats to validity (write these into the report)

- **Synthetic bias:** fixtures you authored resemble your repair rules. Mitigation: public captures and held-out splits.
- **Mutation realism:** simulated changes may not match real redesigns. Mitigation: include real before/after captures where permitted.
- **Small sample:** wide intervals; avoid over-claiming.
- **LLM drift:** model versions change. Mitigation: record versions and cache responses.
- **Ground-truth errors:** audit a sample of expected outputs by hand.

## Ethics and scope

- Public or permitted targets only; respect robots.txt and terms.
- No anti-bot bypass in any benchmark system.
- No client code, client sites or client data anywhere in the benchmark or repository.

## Report template

1. Setup (commit, versions, splits, number of test runs).
2. Main table: B0, B1, B2, P with recovery rate, FAR, review rate, cost, plus counts and intervals.
3. Per-mutation breakdown.
4. Ablations (validation split).
5. Calibration plot.
6. Failure analysis: every false accept, explained.
7. Limitations.
