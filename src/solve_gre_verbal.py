#!/usr/bin/env python3
"""Run and grade LLM solver attempts on GRE-style Verbal Reasoning items."""

import argparse
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "gre_verbal_solver_prompt.md"

SYSTEM_PROMPT = (
    "You are a careful test taker answering GRE-style verbal reasoning questions. "
    "Return only valid JSON with answer labels."
)


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


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_solver_json(text: str) -> Dict[str, Any]:
    cleaned = strip_markdown_fence(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("solver output must be a JSON object")
    return parsed


def normalize_blank(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text in {"", "null", "none"}:
        return None
    match = re.search(r"\d+", text)
    if match:
        return int(match.group(0))
    return text


def normalize_labels(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        labels = re.findall(r"\b[A-Z]\b", value.upper())
        if labels:
            return sorted(set(labels))
        return []
    if isinstance(value, (list, tuple, set)):
        labels: List[str] = []
        for entry in value:
            labels.extend(normalize_labels(entry))
        return sorted(set(labels))
    if isinstance(value, dict):
        for key in ("labels", "label", "answer", "answers", "correct_labels"):
            if key in value:
                return normalize_labels(value[key])
    return []


def expected_answers(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    answers: List[Dict[str, Any]] = []
    for group in item.get("answer_groups", []):
        if not isinstance(group, dict):
            continue
        answers.append(
            {
                "blank": normalize_blank(group.get("blank")),
                "labels": normalize_labels(group.get("correct_labels")),
            }
        )
    return answers


def answer_from_entry(entry: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(entry, dict):
        labels = normalize_labels(entry)
        if labels:
            return {"blank": None, "labels": labels}
        return None

    labels = normalize_labels(
        entry.get("labels")
        if "labels" in entry
        else entry.get("label")
        if "label" in entry
        else entry.get("answer")
        if "answer" in entry
        else entry.get("answers")
        if "answers" in entry
        else entry.get("correct_labels")
    )
    blank = normalize_blank(entry.get("blank") if "blank" in entry else entry.get("blank_index"))
    return {"blank": blank, "labels": labels}


def extract_predicted_answers(parsed: Dict[str, Any], item: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("answers", "answer_groups", "responses"):
        value = parsed.get(key)
        if isinstance(value, list):
            answers = [answer for answer in (answer_from_entry(entry) for entry in value) if answer]
            if answers:
                return answers

    if "labels" in parsed or "label" in parsed or "answer" in parsed:
        labels = normalize_labels(
            parsed.get("labels")
            if "labels" in parsed
            else parsed.get("label")
            if "label" in parsed
            else parsed.get("answer")
        )
        if labels:
            blank = expected_answers(item)[0]["blank"] if len(expected_answers(item)) == 1 else None
            return [{"blank": blank, "labels": labels}]

    blank_answers: List[Dict[str, Any]] = []
    for key, value in parsed.items():
        match = re.fullmatch(r"blank[_\s-]*(\d+)", str(key).lower())
        if match:
            labels = normalize_labels(value)
            if labels:
                blank_answers.append({"blank": int(match.group(1)), "labels": labels})
    return blank_answers


def grade_item_answer(item: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
    expected = expected_answers(item)
    predicted = extract_predicted_answers(parsed, item)
    unmatched = list(predicted)
    missing_blanks: List[Any] = []
    correct = True

    for expected_group in expected:
        expected_blank = expected_group["blank"]
        expected_labels = expected_group["labels"]
        match_index: Optional[int] = None
        for index, predicted_group in enumerate(unmatched):
            if predicted_group["blank"] == expected_blank:
                match_index = index
                break
        if match_index is None and len(expected) == 1 and len(unmatched) == 1:
            match_index = 0

        if match_index is None:
            missing_blanks.append(expected_blank)
            correct = False
            continue

        predicted_group = unmatched.pop(match_index)
        if predicted_group["labels"] != expected_labels:
            correct = False

    if unmatched:
        correct = False

    return {
        "correct": correct,
        "expected": expected,
        "predicted": predicted,
        "missing_blanks": missing_blanks,
    }


def public_item_for_solver(item: Dict[str, Any]) -> Dict[str, Any]:
    public_item = {
        key: value
        for key, value in item.items()
        if key
        not in {
            "answer",
            "correct_answer",
            "correct_labels",
            "explanation",
            "judge",
            "solver_results",
            "solver_accuracy",
        }
    }
    answer_groups: List[Dict[str, Any]] = []
    for group in item.get("answer_groups", []):
        if not isinstance(group, dict):
            continue
        answer_groups.append(
            {
                key: value
                for key, value in group.items()
                if key not in {"correct_labels", "explanation"}
            }
        )
    public_item["answer_groups"] = answer_groups
    return public_item


def render_prompt(template: str, item: Dict[str, Any]) -> str:
    return template.replace(
        "{{ITEM_JSON}}",
        json.dumps(public_item_for_solver(item), ensure_ascii=False, indent=2, sort_keys=True),
    )


def import_generation_components() -> Dict[str, Any]:
    try:
        from datasets import Dataset
        from distilabel.pipeline import Pipeline
        from distilabel.steps.tasks import TextGeneration
    except ImportError as exc:
        raise RuntimeError(
            "Missing solver dependencies. Install them with: pip install -r requirements.txt"
        ) from exc

    try:
        from distilabel.models.llms import OpenAILLM
    except ImportError:
        try:
            from distilabel.llms import OpenAILLM  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Could not import OpenAILLM from Distilabel. Check your distilabel installation."
            ) from exc

    return {
        "Dataset": Dataset,
        "Pipeline": Pipeline,
        "TextGeneration": TextGeneration,
        "OpenAILLM": OpenAILLM,
    }


def unwrap_distiset(distiset: Any) -> List[Dict[str, Any]]:
    keys = list(distiset.keys())
    if not keys:
        return []
    leaf_key = "default" if "default" in keys else keys[0]
    leaf = distiset[leaf_key]
    if hasattr(leaf, "keys") and "train" in list(leaf.keys()):
        leaf = leaf["train"]
    return [dict(row) for row in leaf]


def generation_text(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def run_solver_model(
    items: Sequence[Dict[str, Any]],
    model: str,
    template: str,
    args: argparse.Namespace,
) -> List[Dict[str, Any]]:
    components = import_generation_components()
    Dataset = components["Dataset"]
    Pipeline = components["Pipeline"]
    TextGeneration = components["TextGeneration"]
    OpenAILLM = components["OpenAILLM"]

    rows = [
        {
            "item_id": item.get("id") or f"item-{index}",
            "instruction": render_prompt(template, item),
            "system_prompt": SYSTEM_PROMPT,
        }
        for index, item in enumerate(items, start=1)
    ]
    dataset = Dataset.from_list(rows)

    with Pipeline(name=f"gre-verbal-solver-{re.sub(r'[^A-Za-z0-9_.-]+', '-', model)}") as pipeline:
        TextGeneration(
            name="solve_gre_items",
            llm=OpenAILLM(model=model),
        )

    generation_kwargs: Dict[str, Any] = {
        "temperature": args.temperature,
        "max_new_tokens": args.max_new_tokens,
    }
    if args.response_format_json:
        generation_kwargs["response_format"] = "json"

    distiset = pipeline.run(
        dataset=dataset,
        parameters={
            "solve_gre_items": {
                "llm": {
                    "generation_kwargs": generation_kwargs,
                }
            }
        },
        use_cache=not args.no_cache,
    )

    response_rows: List[Dict[str, Any]] = []
    for row in unwrap_distiset(distiset):
        response_rows.append(
            {
                "item_id": row.get("item_id"),
                "model": model,
                "generation": generation_text(row.get("generation", "")),
            }
        )
    return response_rows


def load_response_rows(path: Path) -> List[Dict[str, Any]]:
    rows = read_jsonl(path)
    for index, row in enumerate(rows, start=1):
        if "item_id" not in row:
            raise ValueError(f"{path}:{index}: response row missing item_id")
        if "model" not in row:
            raise ValueError(f"{path}:{index}: response row missing model")
        if "generation" not in row and "response" not in row and "answer" not in row:
            raise ValueError(f"{path}:{index}: response row missing generation/response/answer")
    return rows


def grade_response(item: Dict[str, Any], response_row: Dict[str, Any]) -> Dict[str, Any]:
    raw_response = response_row.get("generation", response_row.get("response", response_row.get("answer", "")))
    if isinstance(raw_response, dict):
        parsed = raw_response
        raw_text = json.dumps(raw_response, ensure_ascii=False, sort_keys=True)
    else:
        raw_text = str(raw_response)
        try:
            parsed = parse_solver_json(raw_text)
        except Exception as exc:
            return {
                "model": response_row.get("model"),
                "raw_response": raw_text,
                "parse_error": str(exc),
                "correct": False,
                "expected": expected_answers(item),
                "predicted": [],
            }

    graded = grade_item_answer(item, parsed)
    return {
        "model": response_row.get("model"),
        "raw_response": raw_text,
        "parsed_answer": parsed,
        **graded,
    }


def attach_solver_results(
    items: Sequence[Dict[str, Any]],
    response_rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    responses_by_item: Dict[str, List[Dict[str, Any]]] = {}
    for row in response_rows:
        responses_by_item.setdefault(str(row.get("item_id")), []).append(row)

    solved: List[Dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        item_id = str(item.get("id") or f"item-{index}")
        results = [grade_response(item, row) for row in responses_by_item.get(item_id, [])]
        out = dict(item)
        out["solver_results"] = results
        if results:
            out["solver_accuracy"] = round(
                sum(1 for result in results if result.get("correct") is True) / len(results),
                4,
            )
        else:
            out["solver_accuracy"] = None
        solved.append(out)
    return solved


def summarize(solved: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    model_counts: Dict[str, Dict[str, int]] = {}
    total = 0
    correct = 0

    for item in solved:
        for result in item.get("solver_results", []):
            model = str(result.get("model"))
            model_counts.setdefault(model, {"total": 0, "correct": 0})
            model_counts[model]["total"] += 1
            total += 1
            if result.get("correct") is True:
                model_counts[model]["correct"] += 1
                correct += 1

    model_accuracy = {
        model: {
            "total": counts["total"],
            "correct": counts["correct"],
            "accuracy": round(counts["correct"] / counts["total"], 4) if counts["total"] else None,
        }
        for model, counts in sorted(model_counts.items())
    }
    item_accuracies = [
        float(item["solver_accuracy"])
        for item in solved
        if isinstance(item.get("solver_accuracy"), (int, float))
    ]

    return {
        "total_items": len(solved),
        "total_solver_attempts": total,
        "overall_accuracy": round(correct / total, 4) if total else None,
        "average_item_accuracy": round(statistics.mean(item_accuracies), 4) if item_accuracies else None,
        "models": model_accuracy,
    }


def parse_models(args: argparse.Namespace) -> List[str]:
    if args.models:
        models: List[str] = []
        for value in args.models:
            models.extend([part.strip() for part in value.split(",") if part.strip()])
        return models
    env_models = os.environ.get("OPENAI_SOLVER_MODELS")
    if env_models:
        return [part.strip() for part in env_models.split(",") if part.strip()]
    return [os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark GRE-style questions against solver LLMs.")
    parser.add_argument("--input", type=Path, required=True, help="Generated/scored item JSONL.")
    parser.add_argument("--output", type=Path, required=True, help="Solved output JSONL.")
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/solver_summary.json"),
        help="Solver summary JSON output.",
    )
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Solver model names. Accepts space-separated names or comma-separated lists.",
    )
    parser.add_argument(
        "--responses",
        type=Path,
        default=None,
        help="Optional JSONL of prior/mock solver responses. If set, no LLM call is made.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-new-tokens", type=int, default=600)
    parser.add_argument("--no-cache", action="store_true", help="Disable Distilabel cache for solver calls.")
    parser.add_argument(
        "--no-response-format-json",
        dest="response_format_json",
        action="store_false",
        help="Do not pass OpenAI JSON mode via generation kwargs.",
    )
    parser.set_defaults(response_format_json=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = read_jsonl(args.input)
        if args.responses:
            response_rows = load_response_rows(args.responses)
        else:
            template = args.prompt.read_text(encoding="utf-8")
            response_rows = []
            for model in parse_models(args):
                response_rows.extend(run_solver_model(items, model, template, args))
        solved = attach_solver_results(items, response_rows)
        summary = summarize(solved)
        write_jsonl(args.output, solved)
        write_json(args.summary_output, summary)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote solver results for {len(solved)} items to {args.output}")
    print(f"Solver summary written to {args.summary_output}")
    if summary.get("overall_accuracy") is not None:
        print(f"Overall solver accuracy: {summary['overall_accuracy']:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
