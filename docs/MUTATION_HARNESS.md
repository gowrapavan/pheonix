# PHOENIX: Mutation Harness

Status: Draft v0.1

## Purpose

The mutation harness produces **controlled, reproducible website changes with known ground truth**. It is the test oracle for the whole project. It exists from week 1 so every repair strategy is measured the day it is written.

## Principles

1. **Frozen inputs.** Fixtures are saved HTML (and HAR for network-dependent pages), never live sites.
2. **Deterministic.** Every mutation takes a seed; same fixture + mutation + seed gives byte-identical output.
3. **Known expected output.** Each mutation records whether the original data is still recoverable, and what the correct extraction is.
4. **Includes cases where the right answer is "don't repair".**
5. **Mutations are logged.** Each case has a manifest so any result can be traced and reproduced.

## Fixtures

```
benchmarks/fixtures/<site_id>/
  page_001.html          # frozen original (rendered DOM)
  page_001.meta.json     # source, capture date, license/permission note, sha256
  spec.yaml              # extraction spec for this fixture
  expected.json          # ground-truth extraction on the unmutated page
```

Two kinds of fixture:
- **Synthetic** templates you author (full control, safe, good for the first 15).
- **Public captures** from sites that permit it (check robots.txt and terms; record permission in `meta.json`). Never include client targets.

## Mutation catalog (v0.1)

| ID | Mutation | Example | Data recoverable? |
|---|---|---|---|
| M01 | Class rename | `product-price` → `pd-amt` | Yes |
| M02 | ID or attribute removal | drop `id="price"` | Yes |
| M03 | Wrapper insertion | add 1-3 nested `div`s | Yes |
| M04 | Tag change | `div` → `span`, `h2` → `h3` | Yes |
| M05 | Sibling reorder | swap title and price blocks | Yes |
| M06 | Attribute migration | text moves to `data-*` attribute | Yes |
| M07 | Format change | `45000` → `₹45,000.00` | Yes (normalize) |
| M08 | Pagination change | next link → load-more button | Yes |
| M09 | **Decoy insertion** | add "related product" with a price, struck-through old price | Yes, but decoys must not be extracted |
| M10 | Deferred rendering | value injected by JS after load | Yes |
| M11 | A/B variant | two structurally different layouts | Yes |
| M12 | **Content removal** | price element deleted | **No** (correct: reject) |
| M13 | **No-op** | whitespace or comment changes only | n/a (correct: no repair) |
| M14 | **Block page** | CAPTCHA or 429 page replaces content | **No** (correct: classify blocked) |
| M15 | Compound | 2-3 of M01-M11 together | Yes |

Bold rows are the safety tests. A system that repairs M09, M12 or M14 "successfully" has failed.

## Case manifest

Each generated case has a manifest:

```json
{
  "case_id": "shopA-p001-M09-s42",
  "fixture": "shopA/page_001",
  "mutations": [{"id": "M09", "params": {"decoy": "related_price"}}],
  "seed": 42,
  "recoverable": true,
  "expected_output": [{"product_name": "Laptop A", "price": 45000}],
  "expected_decision": "accept_correct_value",
  "mutated_sha256": "..."
}
```

`expected_decision` is one of: `accept_correct_value`, `reject`, `no_action`, `classify_blocked`.

## Repository layout

```
benchmarks/
  fixtures/              # frozen originals
  mutations/             # one module per mutation (pure functions)
  cases/                 # generated manifests + mutated HTML (committed or regenerable by seed)
  baselines/             # B0-B3 implementations
  runner.py
  report.py
```

## Implementation notes

- Mutations are pure functions: `mutate(html, params, seed) -> (html, manifest_entry)`. Use `lxml` or `BeautifulSoup`; never regex on HTML.
- Start with M01-M05, M12, M13 in weeks 1-2; add the rest as repair strategies need them.
- Check that every mutation actually changes the DOM as intended (assert structure diff) and that M13 truly doesn't.
- Rendered-DOM capture for M10 needs Playwright; keep a static-HTML path so most cases run fast without a browser.

## Anti-leakage rules

- Mutation *parameters* (class names, wrapper depth) must be sampled from a space larger than what the repair engine is developed on, so it can't memorize patterns.
- Do not let fixture authorship patterns (naming style) leak into repair heuristics. If you wrote both the fixture and the repair rule in the same sitting, treat that pair as development data only.

## Open questions

- How many fixtures before the first benchmark run? (Suggested: 8 synthetic for weeks 1-4, grow to 30+.)
- Commit mutated HTML, or regenerate from seeds? (Suggested: commit manifests plus hashes, regenerate HTML in CI.)
