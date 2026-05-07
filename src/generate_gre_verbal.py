#!/usr/bin/env python3
"""Generate GRE-style Verbal Reasoning items with Distilabel."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROMPT_VERSION = "gre-verbal-v1"
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "gre_verbal_synthetic_prompt.md"

SYSTEM_PROMPT = (
    "You are an expert assessment writer creating original GRE-style verbal "
    "reasoning benchmark items. You preserve abstract skill and format while "
    "avoiding copied wording, copied answer choices, and seed-specific details. "
    "Return only valid JSON."
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


def render_prompt(template: str, seed: Dict[str, Any], items_per_seed: int) -> str:
    seed_json = json.dumps(seed, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        template.replace("{{ITEMS_PER_SEED}}", str(items_per_seed))
        .replace("{{SEED_JSON}}", seed_json)
    )


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_generation_json(text: str) -> Any:
    cleaned = strip_markdown_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


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


def normalize_items(
    parsed: Any,
    row: Dict[str, Any],
    seed_index: int,
) -> List[Dict[str, Any]]:
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
        items = parsed["items"]
    else:
        raise ValueError("generation must be a JSON object with an 'items' list")

    normalized: List[Dict[str, Any]] = []
    seed_id = row.get("seed_id") or f"seed-{seed_index + 1}"
    for item_index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError("each generated item must be a JSON object")
        out = dict(item)
        out.setdefault("id", f"synthetic-{seed_id}-{item_index:03d}")
        out.setdefault("source_seed_id", seed_id)
        out.setdefault("generation_model", row.get("model_name"))
        out.setdefault("prompt_version", PROMPT_VERSION)
        normalized.append(out)
    return normalized


def import_generation_components() -> Dict[str, Any]:
    try:
        from datasets import Dataset
        from distilabel.pipeline import Pipeline
        from distilabel.steps.tasks import TextGeneration
    except ImportError as exc:
        raise RuntimeError(
            "Missing generation dependencies. Install them with: pip install -r requirements.txt"
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


def build_dataset(
    dataset_cls: Any,
    seed_records: List[Dict[str, Any]],
    template: str,
    items_per_seed: int,
) -> Any:
    rows: List[Dict[str, Any]] = []
    for index, seed in enumerate(seed_records, start=1):
        seed_id = seed.get("seed_id") or f"seed-{index}"
        rows.append(
            {
                "seed_id": seed_id,
                "question_type": seed.get("question_type"),
                "instruction": render_prompt(template, seed, items_per_seed),
                "system_prompt": SYSTEM_PROMPT,
            }
        )
    return dataset_cls.from_list(rows)


def run_pipeline(args: argparse.Namespace) -> List[Dict[str, Any]]:
    components = import_generation_components()
    Pipeline = components["Pipeline"]
    TextGeneration = components["TextGeneration"]
    OpenAILLM = components["OpenAILLM"]

    seed_records = read_jsonl(args.input)
    if not seed_records:
        raise ValueError(f"No seed records found in {args.input}")

    template = args.prompt.read_text(encoding="utf-8")
    dataset = build_dataset(components["Dataset"], seed_records, template, args.items_per_seed)

    model = args.model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"

    with Pipeline(name="gre-verbal-synthetic-generation") as pipeline:
        TextGeneration(
            name="generate_gre_items",
            llm=OpenAILLM(model=model),
        )

    generation_kwargs: Dict[str, Any] = {
        "temperature": args.temperature,
        "max_new_tokens": args.max_new_tokens,
    }
    if args.response_format_json:
        generation_kwargs["response_format"] = "json"

    parameters = {
        "generate_gre_items": {
            "llm": {
                "generation_kwargs": generation_kwargs,
            }
        }
    }

    distiset = pipeline.run(
        dataset=dataset,
        parameters=parameters,
        use_cache=not args.no_cache,
    )

    if args.distiset_dir:
        distiset.save_to_disk(str(args.distiset_dir))

    return unwrap_distiset(distiset)


def postprocess_rows(
    rows: List[Dict[str, Any]],
    output_path: Path,
    raw_output_path: Optional[Path],
    failed_output_path: Optional[Path],
) -> None:
    generated_items: List[Dict[str, Any]] = []
    raw_rows: List[Dict[str, Any]] = []
    failed_rows: List[Dict[str, Any]] = []

    for seed_index, row in enumerate(rows):
        text = generation_text(row.get("generation", ""))
        raw_rows.append(
            {
                "seed_id": row.get("seed_id"),
                "question_type": row.get("question_type"),
                "model_name": row.get("model_name"),
                "generation": text,
            }
        )
        try:
            parsed = parse_generation_json(text)
            generated_items.extend(normalize_items(parsed, row, seed_index))
        except Exception as exc:  # Keep the run useful when one seed fails.
            failed_rows.append(
                {
                    "seed_id": row.get("seed_id"),
                    "question_type": row.get("question_type"),
                    "model_name": row.get("model_name"),
                    "error": str(exc),
                    "generation": text,
                }
            )

    write_jsonl(output_path, generated_items)
    if raw_output_path:
        write_jsonl(raw_output_path, raw_rows)
    if failed_output_path and failed_rows:
        write_jsonl(failed_output_path, failed_rows)

    print(f"Wrote {len(generated_items)} generated items to {output_path}")
    if failed_rows:
        print(f"{len(failed_rows)} generations failed JSON parsing", file=sys.stderr)
        if failed_output_path:
            print(f"Failed generations written to {failed_output_path}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate GRE-style Verbal Reasoning synthetic data with Distilabel."
    )
    parser.add_argument("--input", type=Path, required=True, help="Seed JSONL file.")
    parser.add_argument("--output", type=Path, required=True, help="Generated item JSONL file.")
    parser.add_argument("--raw-output", type=Path, default=None, help="Optional raw LLM generations JSONL.")
    parser.add_argument("--failed-output", type=Path, default=Path("data/failed_generations.jsonl"))
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--distiset-dir", type=Path, default=None, help="Optional Distiset save directory.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL"), help="OpenAI-compatible model name.")
    parser.add_argument("--items-per-seed", type=int, default=2)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--max-new-tokens", type=int, default=2500)
    parser.add_argument("--no-cache", action="store_true", help="Disable Distilabel cache for this run.")
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
        rows = run_pipeline(args)
        postprocess_rows(rows, args.output, args.raw_output, args.failed_output)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
