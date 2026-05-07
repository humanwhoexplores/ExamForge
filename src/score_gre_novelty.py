#!/usr/bin/env python3
"""Score generated GRE- and LSAT-style items for practical novelty against source items."""

import argparse
import json
import re
import statistics
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


DEFAULT_THRESHOLD = 75.0

STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "also",
    "although",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "during",
    "each",
    "even",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "him",
    "his",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "may",
    "more",
    "most",
    "not",
    "of",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "would",
}

CAPITALIZED_EXCLUSIONS = {
    "A",
    "An",
    "And",
    "As",
    "At",
    "Although",
    "Because",
    "But",
    "Choice",
    "Choices",
    "Comprehension",
    "Do",
    "Each",
    "Every",
    "For",
    "GRE",
    "If",
    "In",
    "It",
    "On",
    "Passage",
    "Question",
    "Reading",
    "Reasoning",
    "Seed",
    "Sentence",
    "Some",
    "The",
    "This",
    "Verbal",
    "What",
    "Which",
    "While",
}


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


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_for_match(text: str) -> str:
    lowered = normalize_space(text).lower()
    lowered = re.sub(r"\[[^\]]*blank[^\]]*\]", "blank", lowered)
    lowered = re.sub(r"[^a-z0-9%]+", " ", lowered)
    return normalize_space(lowered)


def source_id(record: Dict[str, Any], index: int) -> str:
    for key in ("seed_id", "id", "question_id", "source_seed_id"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return f"source-{index}"


def tokenize(text: str) -> List[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z'-]*|\d+(?:[.,:/-]\d+)*(?:%| percent)?", text)
    ]


def content_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for token in tokenize(text):
        clean = token.strip("'")
        if len(clean) <= 2:
            continue
        if clean in STOPWORDS:
            continue
        tokens.append(clean)
    return tokens


def ngrams(tokens: Sequence[str], n: int) -> Set[Tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)}


def jaccard(left: Set[Any], right: Set[Any]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def containment(left: Set[Any], right: Set[Any]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def lexical_similarity(left_text: str, right_text: str) -> float:
    left = set(content_tokens(left_text))
    right = set(content_tokens(right_text))
    return min(1.0, 0.65 * jaccard(left, right) + 0.35 * containment(left, right))


def phrase_similarity(left_text: str, right_text: str) -> float:
    left_tokens = content_tokens(left_text)
    right_tokens = content_tokens(right_text)
    scores: List[float] = []
    for size in (3, 4):
        left = ngrams(left_tokens, size)
        right = ngrams(right_tokens, size)
        if left and right:
            scores.append(max(jaccard(left, right), 0.8 * containment(left, right)))
    return max(scores) if scores else 0.0


def parse_labeled_choices(text: str) -> List[str]:
    matches = list(re.finditer(r"(?:^|\s)([A-F])\.\s+", text))
    if not matches:
        return []

    choices: List[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        choice = normalize_space(text[start:end]).strip(" ;,")
        if choice:
            choices.append(choice)
    return choices


def extract_choice_texts(record: Dict[str, Any]) -> List[str]:
    choices: List[str] = []
    answer_groups = record.get("answer_groups")
    if isinstance(answer_groups, list):
        for group in answer_groups:
            if not isinstance(group, dict):
                continue
            for choice in group.get("choices", []):
                if isinstance(choice, dict) and isinstance(choice.get("text"), str):
                    choices.append(choice["text"])

    if choices:
        return choices

    for key in ("source_question", "question", "stem"):
        value = record.get(key)
        if isinstance(value, str):
            parsed = parse_labeled_choices(value)
            if parsed:
                return parsed
    return []


def extract_passage_texts(record: Dict[str, Any]) -> List[str]:
    texts: List[str] = []

    passage = record.get("passage")
    if isinstance(passage, str) and passage.strip():
        texts.append(passage)

    passages = record.get("passages")
    if isinstance(passages, list):
        for entry in passages:
            if isinstance(entry, str) and entry.strip():
                texts.append(entry)
            elif isinstance(entry, dict):
                text = entry.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text)

    return texts


def extract_main_text(record: Dict[str, Any], include_choices: bool = True) -> str:
    parts: List[str] = []
    if isinstance(record.get("source_question"), str):
        parts.append(record["source_question"])
    else:
        stimulus = record.get("stimulus")
        if isinstance(stimulus, str) and stimulus.strip():
            parts.append(stimulus)
        parts.extend(extract_passage_texts(record))
        for key in ("stem", "question"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value)
        if include_choices:
            parts.extend(extract_choice_texts(record))
    return normalize_space(" ".join(parts))


def extract_structure_text(record: Dict[str, Any]) -> str:
    if isinstance(record.get("source_question"), str):
        text = record["source_question"]
        text = re.split(r"\bChoices\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
        return normalize_space(text)
    parts = []
    stimulus = record.get("stimulus")
    if isinstance(stimulus, str) and stimulus.strip():
        parts.append(stimulus)
    parts.extend(extract_passage_texts(record))
    for key in ("stem",):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value)
    return normalize_space(" ".join(parts))


def abstract_structure(text: str) -> str:
    text = re.sub(r"\[[^\]]*blank[^\]]*\]", " BLANK ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+(?:[.,:/-]\d+)*(?:%| percent)?", " NUM ", text)
    text = re.sub(r"[A-Za-z]+", " W ", text)
    text = re.sub(r"(?:\s*W\s*)+", " W ", text)
    return normalize_space(text)


def structure_similarity(left_text: str, right_text: str) -> float:
    left = abstract_structure(left_text)
    right = abstract_structure(right_text)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def normalized_choices(choices: Sequence[str]) -> List[str]:
    return [normalize_for_match(choice) for choice in choices if normalize_for_match(choice)]


def choice_reuse(generated: Dict[str, Any], source: Dict[str, Any]) -> Tuple[float, List[str]]:
    generated_choices = normalized_choices(extract_choice_texts(generated))
    source_choices = normalized_choices(extract_choice_texts(source))
    if not generated_choices or not source_choices:
        return 0.0, []

    copied: List[str] = []
    for generated_choice in generated_choices:
        for source_choice in source_choices:
            ratio = SequenceMatcher(None, generated_choice, source_choice).ratio()
            token_score = jaccard(set(generated_choice.split()), set(source_choice.split()))
            if generated_choice == source_choice or ratio >= 0.92 or token_score >= 0.9:
                copied.append(generated_choice)
                break

    return len(copied) / len(generated_choices), sorted(set(copied))


def extract_distinctive_terms(text: str) -> Set[str]:
    terms: Set[str] = set()
    for number in re.findall(r"\b\d+(?:[.,:/-]\d+)*(?:%| percent)?\b", text):
        terms.add(normalize_for_match(number))

    cleaned = re.sub(r"\b[A-F]\.", " ", text)
    for match in re.finditer(r"\b[A-Z][a-z]+(?:\s+(?:of|and|the|for|in|on|[A-Z][a-z]+))*", cleaned):
        value = normalize_space(match.group(0))
        words = [word for word in value.split() if word.lower() not in {"of", "and", "the", "for", "in", "on"}]
        if not words:
            continue
        if len(words) == 1 and words[0] in CAPITALIZED_EXCLUSIONS:
            continue
        if len(words) == 1 and len(words[0]) <= 3:
            continue
        terms.add(normalize_for_match(value))
    return {term for term in terms if term}


def entity_number_reuse(generated_text: str, source_text: str) -> Tuple[float, List[str]]:
    generated_terms = extract_distinctive_terms(generated_text)
    source_terms = extract_distinctive_terms(source_text)
    reused = sorted(generated_terms & source_terms)
    if not generated_terms:
        return 0.0, []
    return len(reused) / len(generated_terms), reused


def compare_item_to_source(item: Dict[str, Any], source: Dict[str, Any], source_identifier: str) -> Dict[str, Any]:
    item_text = extract_main_text(item)
    source_text = extract_main_text(source)
    item_structure = extract_structure_text(item)
    source_structure = extract_structure_text(source)

    lexical = lexical_similarity(item_text, source_text)
    phrase = phrase_similarity(item_text, source_text)
    structure = structure_similarity(item_structure, source_structure)
    choice, copied_choices = choice_reuse(item, source)
    entity_number, reused_terms = entity_number_reuse(item_text, source_text)

    weighted_similarity = (
        0.35 * lexical
        + 0.20 * phrase
        + 0.20 * choice
        + 0.15 * entity_number
        + 0.10 * structure
    )
    novelty_score = max(0.0, min(100.0, 100.0 * (1.0 - weighted_similarity)))

    return {
        "source_id": source_identifier,
        "novelty_score": round(novelty_score, 1),
        "similarity_score": round(100.0 - novelty_score, 1),
        "components": {
            "lexical_novelty": round(100.0 * (1.0 - lexical), 1),
            "phrase_novelty": round(100.0 * (1.0 - phrase), 1),
            "answer_choice_novelty": round(100.0 * (1.0 - choice), 1),
            "entity_number_novelty": round(100.0 * (1.0 - entity_number), 1),
            "structure_novelty": round(100.0 * (1.0 - structure), 1),
        },
        "copied_answer_choices": copied_choices,
        "reused_distinctive_terms": reused_terms,
    }


def score_item_against_sources(
    item: Dict[str, Any],
    sources: Sequence[Dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> Dict[str, Any]:
    comparisons = [
        compare_item_to_source(item, source, source_id(source, index))
        for index, source in enumerate(sources, start=1)
    ]
    if comparisons:
        riskiest = min(comparisons, key=lambda comparison: comparison["novelty_score"])
    else:
        riskiest = {
            "source_id": None,
            "novelty_score": 100.0,
            "similarity_score": 0.0,
            "components": {
                "lexical_novelty": 100.0,
                "phrase_novelty": 100.0,
                "answer_choice_novelty": 100.0,
                "entity_number_novelty": 100.0,
                "structure_novelty": 100.0,
            },
            "copied_answer_choices": [],
            "reused_distinctive_terms": [],
        }

    reasons: List[str] = []
    if riskiest["novelty_score"] < threshold:
        reasons.append(f"novelty_score below {threshold:g}")
    if riskiest["copied_answer_choices"]:
        reasons.append("copied or near-copied answer choice")
    if riskiest["reused_distinctive_terms"]:
        reasons.append("reused distinctive entity or number")

    scored = dict(item)
    scored["novelty_score"] = riskiest["novelty_score"]
    scored["max_similarity_source_id"] = riskiest["source_id"]
    scored["max_similarity_score"] = riskiest["similarity_score"]
    scored["novelty_components"] = riskiest["components"]
    scored["novelty_pass"] = not reasons
    scored["novelty_reasons"] = reasons or ["passes novelty gate"]
    scored["copied_answer_choices"] = riskiest["copied_answer_choices"]
    scored["reused_distinctive_terms"] = riskiest["reused_distinctive_terms"]
    return scored


def score_records(
    items: Sequence[Dict[str, Any]],
    sources: Sequence[Dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> List[Dict[str, Any]]:
    return [score_item_against_sources(item, sources, threshold) for item in items]


def summarize(scored: Sequence[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
    scores = [float(item.get("novelty_score", 0.0)) for item in scored]
    passed = [item for item in scored if item.get("novelty_pass") is True]
    failed = [item for item in scored if item.get("novelty_pass") is not True]
    summary: Dict[str, Any] = {
        "threshold": threshold,
        "total_items": len(scored),
        "passed_items": len(passed),
        "failed_items": len(failed),
        "average_novelty_score": round(statistics.mean(scores), 1) if scores else None,
        "minimum_novelty_score": round(min(scores), 1) if scores else None,
    }
    reason_counts: Dict[str, int] = {}
    for item in failed:
        for reason in item.get("novelty_reasons", []):
            reason_counts[str(reason)] = reason_counts.get(str(reason), 0) + 1
    summary["failure_reasons"] = reason_counts
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score generated GRE/LSAT-style items for novelty against source/sample JSONL."
    )
    parser.add_argument("--input", type=Path, required=True, help="Generated item JSONL.")
    parser.add_argument(
        "--sources",
        type=Path,
        nargs="+",
        required=True,
        help="One or more source/sample JSONL files to compare against.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Scored output JSONL.")
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/novelty_summary.json"),
        help="Summary JSON output path.",
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = read_jsonl(args.input)
        sources: List[Dict[str, Any]] = []
        for path in args.sources:
            sources.extend(read_jsonl(path))
        scored = score_records(items, sources, args.threshold)
        write_jsonl(args.output, scored)
        summary = summarize(scored, args.threshold)
        write_json(args.summary_output, summary)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {len(scored)} scored items to {args.output}; "
        f"{summary['passed_items']} passed novelty gate."
    )
    print(f"Novelty summary written to {args.summary_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
