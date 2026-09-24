"""Validate a case/export; --purpose training additionally enforces admission."""
import argparse
import sys

from case_contract import read_json, validate_case, validate_export


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--purpose", choices=("structure", "training", "dry-run"), default="structure")
    args = parser.parse_args(argv)
    try:
        value = read_json(args.input)
        if isinstance(value, dict) and "cases" in value:
            validate_export(value)
            cases = value["cases"]
        else:
            cases = [value]
        for case in cases:
            validate_case(case, training=args.purpose == "training")
        print(f"VALID: {len(cases)} case(s); purpose={args.purpose}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
