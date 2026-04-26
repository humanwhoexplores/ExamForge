You are validating a synthetic current-format LSAT-style multiple-choice question.

Return only valid JSON. No markdown, no commentary.

Evaluate the generated item against these criteria:
1. The item matches its declared question type and subtype.
2. The answer key is correct.
3. The explanation is coherent and supports the answer key.
4. The correct answer is fully supported by the stimulus or passage set.
5. Distractors are plausible but wrong for a precise reason.
6. The item has exactly one unambiguous best answer.
7. The item is sufficiently different from the seed.

Subtype-specific checks:
- For logical_reasoning, confirm that the credited response best satisfies the task named in the stem and that no rival answer does so equally well.
- For logical_reasoning, reject items whose reasoning depends on outside knowledge, hidden assumptions not licensed by the stimulus, or copied argumentative structure from the seed.
- For reading_comprehension, confirm that the credited response is supported by the passage or passages and that wrong answers fail by support, scope, attribution, comparison, or force.
- For comparative_passages, confirm that any cross-passage claim respects which passage supports which point.

Similarity policy:
- Reject if the generated item copies or lightly paraphrases the seed.
- Reject if it reuses distinctive named entities, numbers, examples, answer choices, or argumentative structure from the seed.
- Accept only if it preserves abstract skill and difficulty while changing topic and wording.

Return JSON with this schema:
{
  "valid": true,
  "score": 1,
  "issues": ["issue text"],
  "reason": "short explanation",
  "question_type_valid": true,
  "answer_key_valid": true,
  "explanation_valid": true,
  "support_valid": true,
  "distractors_valid": true,
  "best_answer_unambiguous": true,
  "sufficiently_different_from_seed": true
}

Scoring guidance:
- 5: clean, unambiguous, well supported, and clearly distinct from the seed
- 4: strong overall with only minor issues
- 3 or below: reject for benchmark use

Seed record:
{{SEED_JSON}}

Generated item:
{{ITEM_JSON}}
