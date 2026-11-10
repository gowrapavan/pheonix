import argparse
import json
import sys
from pathlib import Path

from phoenix.execution.runner import extract_from_file
from phoenix.spec.loader import load_spec_from_yaml


def check_fixture(fixture_dir: str | Path) -> int:
    path = Path(fixture_dir)
    spec_path = path / "spec.yaml"
    expected_path = path / "expected.json"

    if not spec_path.exists():
        print(f"Error: spec.yaml not found in {fixture_dir}", file=sys.stderr)
        return 1

    spec = load_spec_from_yaml(spec_path)

    html_target_path = Path(spec.target.ref)
    if not html_target_path.exists():
        html_target_path = path / html_target_path.name
    if not html_target_path.exists():
        print(f"Error: target HTML file not found: {spec.target.ref}", file=sys.stderr)
        return 1

    print(f"Checking fixture at: {path}")
    print(f"Spec name: {spec.name} (rev {spec.revision})")
    print(f"Target: {html_target_path}")

    res = extract_from_file(html_target_path, spec)
    print(f"Extracted {res.total_records} record(s). All valid: {res.all_valid}")
    print("Extracted records:")
    print(json.dumps(res.records, indent=2))

    if expected_path.exists():
        expected_data = json.loads(expected_path.read_text(encoding="utf-8"))
        if res.records == expected_data:
            print("[SUCCESS] Extraction matches expected.json")
        else:
            print("[FAIL] Extraction does not match expected.json", file=sys.stderr)
            return 1

    return 0 if res.all_valid else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phoenix", description="Phoenix CLI")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check extraction on a fixture directory")
    check_parser.add_argument("fixture_dir", help="Path to fixture directory containing spec.yaml")

    args = parser.parse_args(argv)

    if args.command == "check":
        return check_fixture(args.fixture_dir)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
