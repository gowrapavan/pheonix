# PHOENIX

PHOENIX is a Python library that detects and repairs broken web-extraction workflows and proves its repairs are correct.

This repository contains the Week 1 foundation implementing:
- Declarative ExtractionSpec validation (Pydantic v2).
- Shared static and Playwright-rendered DOM extraction runner with normalizers and validators.
- SQLite + filesystem snapshot storage with SHA-256 and structural fingerprinting.
- Minimal structural drift detection.
- Deterministic synthetic fixtures and mutation harness (M01 class rename, M05 sibling reorder, M13 no-op).
- Week 1 demo and verification CLI.

---

## Setup (Windows)

Requirements:
- Windows 10/11
- Python 3.12 (available in PATH)

### 1. Create and Activate Virtual Environment
Open PowerShell or Command Prompt:

```cmd
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
```cmd
pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Install Playwright Chromium Browser
```cmd
playwright install chromium
```

---

## Running CLI Check

To check an extraction fixture against its spec and expected ground truth:

```cmd
python -m phoenix.cli check benchmarks/fixtures/shop_a
```

Output:
```text
Checking fixture at: benchmarks/fixtures/shop_a
Spec name: shop_a_fixture (rev 1)
Target: benchmarks/fixtures/shop_a/page_001.html
Extracted 1 record(s). All valid: True
Extracted records:
[
  {
    "title": "Super Laptop X1",
    "price": 45000.0,
    "availability": "In Stock"
  }
]
[SUCCESS] Extraction matches expected.json
```

---

## Running Tests and Linting

Run all tests with coverage:

```cmd
pytest --cov=phoenix --cov=benchmarks tests/
```

Run linter:

```cmd
ruff check .
```
