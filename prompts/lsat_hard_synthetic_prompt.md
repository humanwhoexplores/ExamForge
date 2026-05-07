You are generating a benchmark dataset of fair but difficult current-format LSAT-style multiple-choice questions.

Generate exactly {{ITEMS_PER_SEED}} new questions from the seed record below.

Goal:
- Create questions that remain human-solvable and unambiguous, but are difficult for strong language models because they require exact reasoning rather than surface matching.
- Preserve only the abstract skill, difficulty band, and item family from the seed.
- Do not copy or lightly paraphrase the seed.

Hard constraints:
- Do not reuse distinctive wording, named entities, numbers, examples, scenarios, argumentative structure, or answer choices from the seed.
- Every generated question must have exactly one best answer.
- The correct answer must be fully supported by the stimulus or passage set.
- Distractors must be plausible, grammatically compatible, and wrong for a precise reason.
- Do not rely on trivia, obscure facts, specialized subject-matter knowledge, formal-logic gimmicks, hidden assumptions outside the text, or ambiguous phrasing.
- Do not mention LSAT, LSAC, or the seed question in generated items.
- Return only valid JSON. No markdown, no commentary.

Difficulty design:
- Avoid questions that can be solved by matching a single clue word.
- Make the decisive distinction depend on scope, force, relevance, conditional direction, causation, quantifier control, principle fit, or attribution.
- Wrong answers should often track real language from the stimulus or passage while failing on support, scope, degree, comparison, or logical role.

Logical Reasoning design:
- Use one short stimulus, usually 40-95 words.
- Prefer arguments with layered support, competing explanations, or subtle relevance constraints.
- Strong trap patterns include:
  - scope shifts
  - quantifier shifts
  - reversed conditional direction
  - causation versus correlation
  - answers addressing the wrong issue
  - restatements that sound relevant but do not affect the conclusion
- Use only these subtypes:
  strengthen
  weaken
  necessary_assumption
  sufficient_assumption
  flaw
  method_of_reasoning
  parallel_reasoning
  parallel_flaw
  inference
  principle
  disagreement
  resolve_explain

Reading Comprehension design:
- Use subtype single_passage or comparative_passages only.
- Single passages should usually be 160-280 words.
- Comparative sets should usually use two passages of 100-180 words each.
- Passages should support close reading of structure, attitude, qualification, analogy, principle application, or the effect of new information.
- Trap answers should often reuse real passage language while failing by unsupported extension, overstatement, wrong attribution, mistaken comparison, or subtle scope error.

JSON schema to return:
{
  "items": [
    {
      "question_type": "logical_reasoning | reading_comprehension",
      "subtype": "strengthen | weaken | necessary_assumption | sufficient_assumption | flaw | method_of_reasoning | parallel_reasoning | parallel_flaw | inference | principle | disagreement | resolve_explain | single_passage | comparative_passages",
      "difficulty": 1,
      "skill_tags": ["tag-1", "tag-2"],
      "stimulus": "Short logical reasoning stimulus or null",
      "passage_set_id": "string or null",
      "passages": [
        {"label": "A", "text": "Passage text"}
      ],
      "stem": "Question text",
      "answer_groups": [
        {
          "blank": null,
          "choices": [
            {"label": "A", "text": "choice text"}
          ],
          "correct_labels": ["A"]
        }
      ],
      "explanation": "Concise explanation of why the correct answer is best and why the strongest distractors fail.",
      "difficulty_controls": {
        "requires_precise_reasoning": true,
        "has_plausible_trap_distractors": true,
        "answer_not_from_single_keyword": true,
        "unambiguous_for_humans": true
      },
      "similarity_controls": {
        "new_topic": true,
        "new_wording": true,
        "new_answer_choices": true,
        "no_seed_named_entities": true,
        "no_seed_numbers_or_examples": true,
        "no_seed_argument_structure": true
      }
    }
  ]
}

Field rules:
- For logical_reasoning, use a non-null stimulus, passage_set_id null, and passages null.
- For reading_comprehension, use stimulus null, non-null passage_set_id, and a passages array with one or two objects.
- Every answer group must use blank null.
- Every item must have exactly five answer choices and exactly one correct label.
- difficulty must be an integer from 1 to 5.
- skill_tags must contain 2-5 short lowercase tags.

Seed record:
{{SEED_JSON}}
