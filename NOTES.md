# Engineering Notes: Week 1 Foundation

## Assumptions Made

1. **Structural Fingerprint Representation**:
   - In `EXTRACTION_SPEC.md` and `MUTATION_HARNESS.md`, structural fingerprinting is described as the "tag-path sequence of the record subtree plus a hash that ignores text and whitespace".
   - In M01 class rename, CSS classes are altered, breaking class-based selectors and representing a structural shift in selectors. Including element CSS classes alongside tag names in the node path (e.g. `div.product-price`) ensures that class renames trigger `structurally_changed` drift reports, as required by the Week 1 demo specification, while whitespace and HTML comments trigger `content_changed_only` ("no structural change").
   - If no record root is specified or found, fallback traverses from the HTML body element.

2. **Normalizers**:
   - `strip_currency`: Removes typical currency symbols (`$`, `€`, `£`, `¥`, `₹`) and whitespace.
   - `remove_thousands_separator`: Removes commas from number strings (e.g. `45,000` -> `45000`).
   - Normalizers run before type casting and validators.

3. **Locator Fallback**:
   - Locators for a field are evaluated in order.
   - The first locator whose target element is found, casts successfully, and passes all field validators is selected as winning.
   - If all locators fail, the field returns `success=False` (unless optional) and `status="selector_miss"`, without raising exceptions.

4. **Snapshot Storage**:
   - Metadata is stored in SQLite (`snapshots.db`), including snapshot ID, target ref, spec revision, raw SHA-256, structural hash, tag sequence, timestamp, and relative HTML file path.
   - Raw HTML files are written to disk under the `html/` directory within the store.

5. **Mutation Harness Determinism**:
   - Pure functions `mutate(html, params, seed) -> (html, manifest_entry)` use Python's `random.Random(seed)` with fixed fallback choice pools.
   - Running any mutation twice with the same seed yields byte-identical HTML and identical manifest data.

---

## Spec Ambiguities & Open Questions Addressed

1. **EXTRACTION_SPEC.md Open Questions**:
   - *YAML only, or also a Python builder API?*
     Week 1 provides Pydantic v2 data models (`ExtractionSpec`, `FieldSpec`, `Locator`, etc.) which act as a direct Python builder API, alongside `load_spec_from_yaml` and `validate_spec_dict`.
   - *How are multi-page or multi-step flows represented?*
     `PaginationSpec` is included in `ExtractionSpec` supporting `next_link`, `page_param`, and `infinite_scroll`, reserved for multi-page iteration.
   - *Should `normalize` steps be repairable (format changes), or human-owned like validators?*
     In Week 1, `normalize` steps are defined declaratively in the field spec and executed during extraction. As per `EXTRACTION_SPEC.md`, repair proposals can add/reorder/replace locators, while validators/schema remain human-owned.

2. **Target Path Resolution in CLI**:
   - In `spec.yaml`, `target.ref` can be relative to the fixture directory or repo root. The CLI resolves both gracefully.
