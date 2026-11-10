# PHOENIX: PR/FAQ

Status: Draft v0.1 (Phase 0). Written before any code, to be revised as evidence arrives.

## Press release (draft)

**PHOENIX: an open-source library that keeps web data extraction working when websites change, and proves its repairs are correct.**

Web scrapers break constantly. A site renames a CSS class, wraps content in a new container or moves a price into another element, and a pipeline either crashes or, worse, keeps running while quietly returning wrong data. Maintaining scrapers is one of the largest hidden costs in data engineering.

PHOENIX is a Python library that sits around an existing extraction workflow. It detects structural drift, diagnoses what kind of failure occurred, proposes a repair using deterministic rules, similarity matching and, as a last resort, an LLM, then **independently validates the repair before anything is accepted**. Uncertain repairs go to a human as a pull request. Unsafe repairs are rejected.

PHOENIX is judged on one number above all others: the **false-accept rate**, meaning how often it accepts a repair that returns incorrect data. Every release ships with a reproducible benchmark that reports this rate against three baselines.

## Who is this for?

- Developers and small teams who maintain tens to hundreds of scrapers.
- Data teams whose pipelines depend on third-party pages they don't control.

## What problem does it solve?

Scraper maintenance is reactive. Someone notices missing or wrong data days later, then debugs selectors by hand. PHOENIX turns routine breakage into an automatic, auditable, reversible fix, and makes non-routine breakage visible immediately.

## FAQ

**How is this different from an AI scraper?**
An AI scraper uses an LLM to extract data. PHOENIX maintains extraction you already have. The LLM is the last repair tier and never approves its own output. Verification, confidence gating and measurement are the product.

**How is this different from existing adaptive-selector tools?**
Some existing tools relocate elements after layout changes. A prior-art review (Scrapling and comparable projects) is a Phase 0 task and must be completed before any novelty claim is made. PHOENIX's intended contribution is evidence-based validation, confidence gating and a reproducible benchmark, not the idea of selector repair itself.

**What does "correct" mean?**
Output matches ground truth in the benchmark, and in production it passes schema checks, cross-field invariants and replay against held-out historical snapshots. A successful selector run or HTTP 200 never counts as correct.

**What does PHOENIX do when a site is blocked, down or rate limiting?**
It classifies the failure as *blocked/unavailable* and does not attempt a repair. It never tries to bypass anti-bot or access controls.

**What if the data genuinely disappeared from the page?**
The correct outcome is rejection and a human alert. Rejecting an unrecoverable case counts as a success in the benchmark.

**Does it work without paid services?**
Yes. The core (deterministic and similarity repair, validation, benchmark) must run fully offline with local Chromium and SQLite. LLM repair is optional.

**Will it be a SaaS?**
Possibly, later, and only if outside users want it. The order is: open-source core, then benchmark and research, then hosted product.

## Non-goals for v0.1

- Not a general-purpose scraper, crawler or proxy network.
- Not an anti-bot bypass tool.
- No dashboard, team accounts, billing or distributed workers.
- No cross-site learning (requires benchmark data first).
- No claim of research novelty until prior-art review is done.

## Rules for the project

1. The core library works without the dashboard, database server or any LLM.
2. The LLM never approves its own repair; the validator decides.
3. Every accepted repair has recorded evidence and is versioned and reversible.
4. Benchmark and public examples use only public, permitted targets or synthetic fixtures. **No client code, client sites or client data enters this repository.**
5. Respect robots.txt and site terms in anything that touches a live site.

## v0.1 success criteria

These are acceptance criteria, not claims about current performance.

- Python SDK and CLI installable by a stranger in under 10 minutes.
- Drift detection, failure diagnosis and at least one deterministic repair strategy.
- Held-out validation and a confidence gate with accept, review and reject outcomes.
- Frozen, reproducible benchmark with three baselines plus PHOENIX.
- Zero unvalidated automatic repairs.
- Failures and false accepts reported honestly in the benchmark report.
