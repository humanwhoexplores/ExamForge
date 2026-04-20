You are validating a synthetic GRE-style Verbal Reasoning question.

Return only valid JSON. No markdown, no commentary.

Evaluate the generated item against these criteria:
1. The item matches its declared question type and subtype.
2. The answer key is correct.
3. The explanation is coherent and supports the answer key.
4. Distractors are plausible but wrong.
5. The item is sufficiently different from the seed.
6. For sentence equivalence, exactly two answers produce equivalent completed meanings.
7. For text completion, each blank has exactly one correct answer and the blanks interact logically when multi-blank.
8. For reading comprehension, the answer is fully supported by the passage.

Similarity policy:
- Reject if the generated item copies or lightly paraphrases the seed.
- Reject if it reuses distinctive named entities, numbers, examples, answer choices, or sentence structure from the seed.
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
  "distractors_valid": true,
  "sufficiently_different_from_seed": true
}

Seed record:
{{SEED_JSON}}

Generated item:
{{ITEM_JSON}}

