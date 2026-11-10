# PHOENIX: Extraction Specification

Status: Draft v0.1

## Purpose

The extraction spec is the declarative description of one extraction task: where the data is, what it should look like, and how to know it is correct. PHOENIX repairs **the spec**, never arbitrary user code. This keeps repairs small, diffable, testable and reversible.

## Design rules

1. **Spec is data, not code.** YAML or JSON, validated by Pydantic v2.
2. **Repairs only touch the `locators` section.** Schema, validators and invariants are human-owned; a repair can never loosen them.
3. **Every change creates a new version.** Specs are immutable once versioned; repairs are diffs between versions.
4. **Ground truth lives next to the spec** (golden examples), not inside the repair engine.

## Format

```yaml
spec_version: 1
name: product-page
revision: 4                      # incremented on every accepted change
target:
  kind: fixture                  # fixture | url
  ref: fixtures/shop_a/product_001.html
  wait_for: ".product-card"      # optional readiness condition

record:
  root: ".product-card"          # one record per match

fields:
  product_name:
    type: string
    required: true
    locators:                    # ordered; first that passes wins
      - { kind: css, value: "h2.product-title" }
      - { kind: css, value: "[data-product-name]" }
    validators:
      - { kind: non_empty }
      - { kind: max_length, value: 200 }

  price:
    type: decimal
    required: true
    locators:
      - { kind: css, value: ".product-price" }
    normalize: [strip_currency, remove_thousands_separator]
    validators:
      - { kind: range, min: 0, max: 10000000 }

  availability:
    type: enum
    values: ["In Stock", "Out of Stock"]
    required: false
    locators:
      - { kind: css, value: ".availability" }

pagination:                      # optional
  kind: next_link                # next_link | page_param | infinite_scroll
  locator: { kind: css, value: "a[rel=next]" }
  max_pages: 5

invariants:                      # cross-field and cross-record rules
  - { kind: expr, rule: "price > 0 if availability == 'In Stock'" }
  - { kind: unique, field: product_name }
  - { kind: record_count, min: 1 }

golden:                          # ground truth for regression replay
  - snapshot: snapshots/product_001_rev1.html
    expected:
      - { product_name: "Laptop A", price: 45000, availability: "In Stock" }

repair_policy:
  allow_auto: true
  max_tier: llm                  # deterministic | similarity | llm
  require_review_if:
    - field_in: [price]          # sensitive fields always get stricter gates
  min_heldout_snapshots: 3
```

## Locator kinds

| Kind | Example | Notes |
|---|---|---|
| `css` | `.product-price` | Primary form |
| `xpath` | `//h2[@data-name]` | When CSS can't express it |
| `text_anchor` | label "Price" → adjacent value | Survives class renames |
| `attr` | `[data-price]` | Prefer stable attributes |
| `relative` | sibling or parent of another locator | For structure-based recovery |

## Validators vs invariants

- **Validators** check one field in isolation (type, range, format).
- **Invariants** check relationships (price present when in stock, no duplicate records, record count in an expected band).
- Both are human-owned and cannot be modified by a repair.

## Repair proposal format

A repair is a patch against one revision of the spec:

```yaml
proposal_id: rp_0192
base_revision: 4
field: price
change:
  add_locator: { kind: attr, value: "[data-price]" }
  position: 0
tier: deterministic
evidence:
  validators_passed: true
  invariants_passed: true
  heldout_snapshots_passed: 3/3
  agreement_across_tiers: true
decision: accept | review | reject
```

A proposal can add, reorder or replace locators only. It cannot change `type`, `validators`, `invariants` or `golden`.

## Failure taxonomy (used by diagnosis)

| Class | Meaning | Repair attempted? |
|---|---|---|
| `selector_miss` | Locator matches nothing | Yes |
| `structure_shift` | Element exists but moved or wrapped | Yes |
| `format_change` | Value present but format changed | Yes (normalize) |
| `pagination_change` | Next-page mechanism changed | Yes |
| `content_removed` | Data is genuinely gone | **No: alert human** |
| `blocked` | CAPTCHA, 403, 429, bot wall | **No: never bypass** |
| `unavailable` | Timeout, 5xx, DNS failure | **No: retry/alert** |
| `no_change` | Page identical or equivalent | No (false-alarm control) |

## Open questions (resolve in Phase 0)

- YAML only, or also a Python builder API?
- How are multi-page or multi-step flows represented?
- Should `normalize` steps be repairable (format changes), or human-owned like validators?
