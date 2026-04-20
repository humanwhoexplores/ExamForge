#!/usr/bin/env python3
"""Run an LLM judge over generated GRE-style Verbal Reasoning items."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "gre_verbal_judge_prompt.md"

SYSTEM_PROMPT = (
    "You are a strict GRE verbal item reviewer. You validate format, answer key, "
    "reasoning quality, distractor quality, and seed dissimilarity. Return only JSON."
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


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_generation_json(text: str) -> Dict[str, Any]:
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
        raise ValueError("judge output must be a JSON object")
    return parsed


def import_generation_components() -> Dict[str, Any]:
    try:
        from datasets import Dataset
        from distilabel.pipeline import Pipeline
        from distilabel.steps.tasks import TextGeneration
    except ImportError as exc:
        raise RuntimeError(
            "Missing judge dependencies. Install them with: pip install -r requirements.txt"
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


def render_prompt(template: str, seed: Dict[str, Any], item: Dict[str, Any]) -> str:
    return (
        template.replace("{{SEED_JSON}}", json.dumps(seed, ensure_ascii=False, indent=2, sort_keys=True))
        .replace("{{ITEM_JSON}}", json.dumps(item, ensure_ascii=False, indent=2, sort_keys=True))
    )


def load_seed_map(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if path is None:
        return {}
    seeds = read_jsonl(path)
    seed_map: Dict[str, Dict[str, Any]] = {}
    for index, seed in enumerate(seeds, start=1):
        seed_id = seed.get("seed_id") or seed.get("question_id") or f"seed-{index}"
        seed_map[str(seed_id)] = seed
    return seed_map


def build_dataset(dataset_cls: Any, items: List[Dict[str, Any]], seed_map: Dict[str, Dict[str, Any]], template: str) -> Any:
    rows: List[Dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        item_id = item.get("id") or f"item-{index}"
        seed_id = item.get("source_seed_id")
        seed = seed_map.get(str(seed_id), {}) if seed_id is not None else {}
        rows.append(
            {
                "item_id": item_id,
                "source_seed_id": seed_id,
                "instruction": render_prompt(template, seed, item),
                "system_prompt": SYSTEM_PROMPT,
            }
        )
    return dataset_cls.from_list(rows)


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


def run_judge(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    components = import_generation_components()
    Pipeline = components["Pipeline"]
    TextGeneration = components["TextGeneration"]
    OpenAILLM = components["OpenAILLM"]

    items = read_jsonl(args.input)
    seed_map = load_seed_map(args.seeds)
    template = args.prompt.read_text(encoding="utf-8")
    dataset = build_dataset(components["Dataset"], items, seed_map, template)

    model = args.model or os.environ.get("OPENAI_JUDGE_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o"

    with Pipeline(name="gre-verbal-judge") as pipeline:
        TextGeneration(
            name="judge_gre_items",
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
            "judge_gre_items": {
                "llm": {
                    "generation_kwargs": generation_kwargs,
                }
            }
        },
        use_cache=not args.no_cache,
    )

    rows = unwrap_distiset(distiset)
    accepted: List[Dict[str, Any]] = []
    reviewed: List[Dict[str, Any]] = []
    item_by_id = {str(item.get("id")): item for item in items}

    for row in rows:
        item_id = str(row.get("item_id"))
        item = dict(item_by_id.get(item_id, {}))
        raw_judgment = generation_text(row.get("generation", ""))
        try:
            judgment = parse_generation_json(raw_judgment)
        except Exception as exc:
            judgment = {
                "valid": False,
                "score": 1,
                "issues": [f"judge output parse failure: {exc}"],
                "reason": raw_judgment,
            }
        item["judge"] = judgment
        reviewed.append(item)
        if judgment.get("valid") is True and int(judgment.get("score", 0)) >= args.min_score:
            accepted.append(item)

    return accepted, reviewed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge generated GRE-style Verbal JSONL with an LLM.")
    parser.add_argument("--input", type=Path, required=True, help="Generated item JSONL file.")
    parser.add_argument("--accepted-output", type=Path, required=True, help="Accepted judged items JSONL file.")
    parser.add_argument("--reviewed-output", type=Path, default=Path("data/reviewed_gre_verbal.jsonl"))
    parser.add_argument("--seeds", type=Path, default=None, help="Optional seed JSONL for similarity checks.")
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--model", default=os.environ.get("OPENAI_JUDGE_MODEL"), help="OpenAI-compatible judge model.")
    parser.add_argument("--min-score", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-new-tokens", type=int, default=900)
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
        accepted, reviewed = run_judge(args)
        write_jsonl(args.accepted_output, accepted)
        write_jsonl(args.reviewed_output, reviewed)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(accepted)} accepted items to {args.accepted_output}")
    print(f"Wrote {len(reviewed)} reviewed items to {args.reviewed_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

