from __future__ import annotations

import argparse
from typing import Any, Dict

from edgebench.commands.enrich_result import enrich_result_to_path
from edgebench.compare.comparator import compare_results
from edgebench.compare.judgement import judge_comparison
from edgebench.result.loader import load_result


def run_enriched_accuracy_demo(
    *,
    base_result: str,
    base_accuracy_json: str,
    new_result: str,
    new_accuracy_json: str,
    out_dir: str = "results_enriched",
    overwrite_accuracy: bool = True,
) -> Dict[str, Any]:
    saved_base_path = enrich_result_to_path(
        result_path=base_result,
        accuracy_json=base_accuracy_json,
        out_dir=out_dir,
        overwrite_accuracy=overwrite_accuracy,
    )
    saved_new_path = enrich_result_to_path(
        result_path=new_result,
        accuracy_json=new_accuracy_json,
        out_dir=out_dir,
        overwrite_accuracy=overwrite_accuracy,
    )

    base_loaded = load_result(saved_base_path)
    new_loaded = load_result(saved_new_path)
    compare_result = compare_results(base_loaded, new_loaded)
    judgement = judge_comparison(compare_result)

    return {
        "saved_base_path": saved_base_path,
        "saved_new_path": saved_new_path,
        "compare_result": compare_result,
        "judgement": judgement,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enrich two structured results with external accuracy JSON and run compare/judgement."
    )
    parser.add_argument("--base-result", required=True)
    parser.add_argument("--base-accuracy-json", required=True)
    parser.add_argument("--new-result", required=True)
    parser.add_argument("--new-accuracy-json", required=True)
    parser.add_argument("--out-dir", default="results_enriched")
    parser.add_argument(
        "--no-overwrite-accuracy",
        action="store_true",
        help="Fail if a source result already contains accuracy metadata.",
    )
    parser.add_argument("--expect-overall", default="")
    parser.add_argument("--expect-tradeoff-risk", default="")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    result = run_enriched_accuracy_demo(
        base_result=args.base_result,
        base_accuracy_json=args.base_accuracy_json,
        new_result=args.new_result,
        new_accuracy_json=args.new_accuracy_json,
        out_dir=args.out_dir,
        overwrite_accuracy=not args.no_overwrite_accuracy,
    )

    compare_result = result["compare_result"]
    judgement = result["judgement"]

    print(f"Saved base path : {result['saved_base_path']}")
    print(f"Saved new path  : {result['saved_new_path']}")
    print(f"Comparison mode : {compare_result['precision']['comparison_mode']}")
    print(f"Primary metric  : {compare_result['accuracy']['metric_name']}")
    print(f"Overall         : {judgement['overall']}")
    print(f"Trade-off risk  : {judgement['tradeoff_risk']}")
    print(f"Summary         : {judgement['summary']}")

    if args.expect_overall and judgement["overall"] != args.expect_overall:
        print(
            f"Expected overall {args.expect_overall!r}, but got {judgement['overall']!r}."
        )
        return 1

    if args.expect_tradeoff_risk and judgement["tradeoff_risk"] != args.expect_tradeoff_risk:
        print(
            "Expected tradeoff_risk "
            f"{args.expect_tradeoff_risk!r}, but got {judgement['tradeoff_risk']!r}."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
