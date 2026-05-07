#!/usr/bin/env python3
"""Filter GRE-style generated items using validation, judge, novelty, and solver results."""

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from validate_dataset import validate_record
except ImportError:  # pragma: no cover - useful when imported as src.filter_gre_verbal
    from src.validate_dataset import validate_record  # type: ignore


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            records.append(record)
    return records


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def solver_results(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    value = item.get("solver_results")
    if isinstance(value, list):
        return [result for result in value if isinstance(result, dict)]
    return []


def solver_accuracy(item: Dict[str, Any]) -> Optional[float]:
    existing = item.get("solver_accuracy")
    if isinstance(existing, (int, float)):
        return float(existing)

    results = solver_results(item)
    if not results:
        return None
    return sum(1 for result in results if result.get("correct") is True) / len(results)


def judge_score(item: Dict[str, Any]) -> Optional[float]:
    judge = item.get("judge")
    if not isinstance(judge, dict):
        return None
    score = judge.get("score")
    if isinstance(score, (int, float)):
        return float(score)
    return None


def evaluate_item(item: Dict[str, Any], line_number: int, args: argparse.Namespace) -> Tuple[bool, List[str]]:
    issues: List[str] = []

    for error in validate_record(item, line_number):
        issues.append(f"schema: {error}")

    judge = item.get("judge")
    if isinstance(judge, dict):
        if judge.get("valid") is not True:
            issues.append("judge: item is not valid")
        score = judge.get("score")
        if isinstance(score, (int, float)) and float(score) < args.min_judge_score:
            issues.append(f"judge: score below {args.min_judge_score:g}")
    elif not args.allow_unjudged:
        issues.append("judge: missing judge result")

    novelty_score = item.get("novelty_score")
    if isinstance(novelty_score, (int, float)):
        if float(novelty_score) < args.min_novelty:
            issues.append(f"novelty: score below {args.min_novelty:g}")
    elif not args.allow_unscored:
        issues.append("novelty: missing novelty_score")

    if item.get("novelty_pass") is False:
        reasons = item.get("novelty_reasons")
        if isinstance(reasons, list) and reasons:
            issues.append("novelty: " + "; ".join(str(reason) for reason in reasons))
        else:
            issues.append("novelty: failed novelty gate")

    accuracy = solver_accuracy(item)
    if accuracy is None:
        if not args.allow_unsolved:
            issues.append("solver: missing solver results")
    elif args.max_item_solver_accuracy is not None and accuracy > args.max_item_solver_accuracy:
        issues.append(f"solver: item accuracy above {args.max_item_solver_accuracy:g}")

    return not issues, issues


def hardness_sort_key(item: Dict[str, Any]) -> Tuple[float, float, float, float, str]:
    accuracy = solver_accuracy(item)
    if accuracy is None:
        accuracy = 1.0
    difficulty = item.get("difficulty")
    novelty = item.get("novelty_score")
    score = judge_score(item)
    return (
        accuracy,
        -float(difficulty) if isinstance(difficulty, (int, float)) else 0.0,
        -float(novelty) if isinstance(novelty, (int, float)) else 0.0,
        -float(score) if isinstance(score, (int, float)) else 0.0,
        str(item.get("id") or ""),
    )


def dataset_solver_accuracy(items: Sequence[Dict[str, Any]]) -> Optional[float]:
    accuracies = [solver_accuracy(item) for item in items]
    numeric = [accuracy for accuracy in accuracies if accuracy is not None]
    if not numeric:
        return None
    return statistics.mean(numeric)


def filter_items(items: Sequence[Dict[str, Any]], args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for line_number, item in enumerate(items, start=1):
        passed, issues = evaluate_item(item, line_number, args)
        if passed:
            candidates.append(dict(item))
        else:
            rejected_item = dict(item)
            rejected_item["filter_issues"] = issues
            rejected.append(rejected_item)

    candidates.sort(key=hardness_sort_key)
    accepted = candidates[: args.target_size] if args.target_size else list(candidates)

    if args.enforce_solver_target:
        while accepted:
            accuracy = dataset_solver_accuracy(accepted)
            if accuracy is None or accuracy <= args.max_dataset_solver_accuracy:
                break
            rejected_item = dict(accepted.pop())
            rejected_item["filter_issues"] = [
                f"solver: removed to meet dataset accuracy target {args.max_dataset_solver_accuracy:g}"
            ]
            rejected.append(rejected_item)

    final_accuracy = dataset_solver_accuracy(accepted)
    summary = {
        "input_items": len(items),
        "candidate_items": len(candidates),
        "accepted_items": len(accepted),
        "rejected_items": len(rejected),
        "target_size": args.target_size or None,
        "min_novelty": args.min_novelty,
        "min_judge_score": args.min_judge_score,
        "max_dataset_solver_accuracy": args.max_dataset_solver_accuracy,
        "dataset_solver_accuracy": round(final_accuracy, 4) if final_accuracy is not None else None,
        "solver_accuracy_target_met": (
            final_accuracy is not None and final_accuracy <= args.max_dataset_solver_accuracy
        )
        if accepted
        else False,
        "enforced_solver_target": args.enforce_solver_target,
    }

    issue_counts: Dict[str, int] = {}
    for item in rejected:
        for issue in item.get("filter_issues", []):
            issue_counts[str(issue)] = issue_counts.get(str(issue), 0) + 1
    summary["rejection_reasons"] = issue_counts

    return accepted, rejected, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter GRE-style generated items using judge, novelty, and solver results."
    )
    parser.add_argument("--input", type=Path, required=True, help="Reviewed/scored/solved item JSONL.")
    parser.add_argument("--output", type=Path, required=True, help="Accepted output JSONL.")
    parser.add_argument(
        "--rejected-output",
        type=Path,
        default=Path("data/rejected_gre_verbal.jsonl"),
        help="Rejected item JSONL output.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/filter_summary.json"),
        help="Filter summary JSON output.",
    )
    parser.add_argument("--target-size", type=int, default=0, help="Optional accepted dataset size cap.")
    parser.add_argument("--min-novelty", type=float, default=75.0)
    parser.add_argument("--min-judge-score", type=float, default=4.0)
    parser.add_argument("--max-dataset-solver-accuracy", type=float, default=0.85)
    parser.add_argument(
        "--max-item-solver-accuracy",
        type=float,
        default=None,
        help="Optional per-item solver accuracy gate.",
    )
    parser.add_argument(
        "--enforce-solver-target",
        action="store_true",
        help="Drop easiest accepted items until dataset solver accuracy is at or below the target.",
    )
    parser.add_argument("--allow-unjudged", action="store_true", help="Do not require judge results.")
    parser.add_argument("--allow-unscored", action="store_true", help="Do not require novelty results.")
    parser.add_argument("--allow-unsolved", action="store_true", help="Do not require solver results.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = read_jsonl(args.input)
        accepted, rejected, summary = filter_items(items, args)
        write_jsonl(args.output, accepted)
        write_jsonl(args.rejected_output, rejected)
        write_json(args.summary_output, summary)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(accepted)} accepted items to {args.output}")
    print(f"Wrote {len(rejected)} rejected items to {args.rejected_output}")
    print(f"Filter summary written to {args.summary_output}")
    if summary.get("dataset_solver_accuracy") is not None:
        print(f"Accepted dataset solver accuracy: {summary['dataset_solver_accuracy']:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
