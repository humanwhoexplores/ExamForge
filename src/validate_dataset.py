#!/usr/bin/env python3
"""Validate generated GRE- and LSAT-style dataset JSONL files."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


VALID_TYPES = {
    "text_completion",
    "sentence_equivalence",
    "reading_comprehension",
    "logical_reasoning",
}

LSAT_LOGICAL_REASONING_SUBTYPES = {
    "strengthen",
    "weaken",
    "necessary_assumption",
    "sufficient_assumption",
    "flaw",
    "method_of_reasoning",
    "parallel_reasoning",
    "parallel_flaw",
    "inference",
    "principle",
    "disagreement",
    "resolve_explain",
}

LSAT_READING_COMPREHENSION_SUBTYPES = {"single_passage", "comparative_passages"}


def read_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
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
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            yield line_number, record


def labels_for_group(group: Dict[str, Any]) -> List[str]:
    choices = group.get("choices")
    if not isinstance(choices, list) or not choices:
        return []
    labels: List[str] = []
    for choice in choices:
        if isinstance(choice, dict) and isinstance(choice.get("label"), str):
            labels.append(choice["label"])
    return labels


def validate_answer_group(group: Dict[str, Any], line_number: int) -> List[str]:
    errors: List[str] = []
    if not isinstance(group, dict):
        return [f"line {line_number}: answer group must be an object"]

    labels = labels_for_group(group)
    if not labels:
        errors.append(f"line {line_number}: answer group has no labeled choices")
    if len(labels) != len(set(labels)):
        errors.append(f"line {line_number}: duplicate choice labels in answer group")

    correct = group.get("correct_labels")
    if not isinstance(correct, list) or not correct:
        errors.append(f"line {line_number}: answer group missing correct_labels")
    else:
        missing = [label for label in correct if label not in labels]
        if missing:
            errors.append(f"line {line_number}: correct labels not found in choices: {missing}")

    for choice in group.get("choices", []):
        if not isinstance(choice, dict):
            errors.append(f"line {line_number}: choice must be an object")
            continue
        if not isinstance(choice.get("label"), str) or not choice["label"].strip():
            errors.append(f"line {line_number}: choice missing label")
        if not isinstance(choice.get("text"), str) or not choice["text"].strip():
            errors.append(f"line {line_number}: choice missing text")

    return errors


def validate_passages(passages: Any, line_number: int) -> List[str]:
    errors: List[str] = []
    if not isinstance(passages, list) or not passages:
        return [f"line {line_number}: passages must be a non-empty list"]

    labels: List[str] = []
    for index, passage in enumerate(passages, start=1):
        if isinstance(passage, str):
            if not passage.strip():
                errors.append(f"line {line_number}: passage {index} must be a non-empty string")
            continue

        if not isinstance(passage, dict):
            errors.append(f"line {line_number}: passage {index} must be a string or object")
            continue

        text = passage.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"line {line_number}: passage {index} missing text")

        if "label" in passage:
            label = passage.get("label")
            if not isinstance(label, str) or not label.strip():
                errors.append(f"line {line_number}: passage {index} has invalid label")
            else:
                labels.append(label)

    if len(labels) != len(set(labels)):
        errors.append(f"line {line_number}: duplicate passage labels")

    return errors


def validate_single_best_answer_item(
    answer_groups: List[Dict[str, Any]],
    line_number: int,
    question_label: str,
) -> List[str]:
    errors: List[str] = []
    if len(answer_groups) != 1:
        errors.append(f"line {line_number}: {question_label} must have one answer group")
        return errors

    group = answer_groups[0]
    if not isinstance(group, dict):
        errors.append(f"line {line_number}: {question_label} answer group must be an object")
        return errors

    choices = group.get("choices", [])
    correct = group.get("correct_labels", [])

    if group.get("blank") is not None:
        errors.append(f"line {line_number}: {question_label} answer group must use blank null")
    if len(choices) != 5:
        errors.append(f"line {line_number}: {question_label} must have exactly five choices")
    if len(correct) != 1:
        errors.append(f"line {line_number}: {question_label} must have exactly one correct label")

    return errors


def validate_record(record: Dict[str, Any], line_number: int) -> List[str]:
    errors: List[str] = []

    for field in ["id", "question_type", "stem", "answer_groups", "explanation"]:
        if field not in record:
            errors.append(f"line {line_number}: missing required field '{field}'")

    question_type = record.get("question_type")
    if question_type not in VALID_TYPES:
        errors.append(f"line {line_number}: invalid question_type '{question_type}'")

    if not isinstance(record.get("stem"), str) or not record.get("stem", "").strip():
        errors.append(f"line {line_number}: stem must be a non-empty string")
    if not isinstance(record.get("explanation"), str) or not record.get("explanation", "").strip():
        errors.append(f"line {line_number}: explanation must be a non-empty string")

    answer_groups = record.get("answer_groups")
    if not isinstance(answer_groups, list) or not answer_groups:
        errors.append(f"line {line_number}: answer_groups must be a non-empty list")
        return errors

    for group in answer_groups:
        errors.extend(validate_answer_group(group, line_number))

    if question_type == "text_completion":
        if len(answer_groups) not in {1, 2, 3}:
            errors.append(f"line {line_number}: text_completion must have 1-3 answer groups")
        for group in answer_groups:
            correct = group.get("correct_labels") if isinstance(group, dict) else None
            if isinstance(correct, list) and len(correct) != 1:
                errors.append(f"line {line_number}: each text_completion blank needs exactly one answer")

    if question_type == "sentence_equivalence":
        if len(answer_groups) != 1:
            errors.append(f"line {line_number}: sentence_equivalence must have one answer group")
        else:
            group = answer_groups[0]
            choices = group.get("choices", []) if isinstance(group, dict) else []
            correct = group.get("correct_labels", []) if isinstance(group, dict) else []
            if len(choices) != 6:
                errors.append(f"line {line_number}: sentence_equivalence must have exactly six choices")
            if len(correct) != 2:
                errors.append(f"line {line_number}: sentence_equivalence must have exactly two correct labels")

    if question_type == "reading_comprehension":
        subtype = record.get("subtype")
        passages = record.get("passages")
        uses_lsat_rc_schema = (
            subtype in LSAT_READING_COMPREHENSION_SUBTYPES
            or passages is not None
            or record.get("passage_set_id") is not None
        )

        if uses_lsat_rc_schema:
            if subtype not in LSAT_READING_COMPREHENSION_SUBTYPES:
                errors.append(
                    f"line {line_number}: invalid LSAT reading_comprehension subtype '{subtype}'"
                )
            if not isinstance(record.get("passage_set_id"), str) or not record.get("passage_set_id", "").strip():
                errors.append(f"line {line_number}: LSAT reading_comprehension must include passage_set_id")
            errors.extend(validate_single_best_answer_item(answer_groups, line_number, "LSAT reading_comprehension"))
            errors.extend(validate_passages(passages, line_number))
            if isinstance(passages, list):
                expected_passage_count = 2 if subtype == "comparative_passages" else 1
                if len(passages) != expected_passage_count:
                    errors.append(
                        f"line {line_number}: subtype '{subtype}' requires {expected_passage_count} passage"
                        f"{'' if expected_passage_count == 1 else 's'}"
                    )
        elif not isinstance(record.get("passage"), str) or not record.get("passage", "").strip():
            errors.append(f"line {line_number}: reading_comprehension must include a passage")

    if question_type == "logical_reasoning":
        subtype = record.get("subtype")
        if subtype not in LSAT_LOGICAL_REASONING_SUBTYPES:
            errors.append(f"line {line_number}: invalid logical_reasoning subtype '{subtype}'")
        if not isinstance(record.get("stimulus"), str) or not record.get("stimulus", "").strip():
            errors.append(f"line {line_number}: logical_reasoning must include a stimulus")
        errors.extend(validate_single_best_answer_item(answer_groups, line_number, "logical_reasoning"))

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated GRE/LSAT-style JSONL.")
    parser.add_argument("path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    total = 0
    errors: List[str] = []
    try:
        for line_number, record in read_jsonl(args.path):
            total += 1
            errors.extend(validate_record(record, line_number))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s) across {total} row(s).", file=sys.stderr)
        return 1

    print(f"Validation passed: {total} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
