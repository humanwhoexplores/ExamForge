You are generating a benchmark dataset of current-format LSAT-style multiple-choice questions.

Generate exactly {{ITEMS_PER_SEED}} new questions from the seed record below.

Scope:
- Use only these question families: logical_reasoning and reading_comprehension.
- Match the seed's abstract skill, difficulty band, and item family.
- Preserve only the underlying reasoning task and format, not the seed's surface content.

Hard constraints:
- Do not copy or lightly paraphrase the seed question.
- Do not reuse distinctive wording, named entities, numbers, examples, scenarios, or answer choices from the seed.
- Every generated question must have exactly one best answer.
- The correct answer must be fully supported by the stimulus or passage set.
- Distractors must be plausible, attractive, and wrong for a precise reason.
- Do not rely on outside knowledge, specialized jargon, formal-logic notation, or tricks.
- Do not mention LSAT, LSAC, the seed question, or any source material in the generated items.
- Return only valid JSON. No markdown, no commentary.

Question-family requirements:

1. logical_reasoning
- Use one short stimulus, typically 35-90 words.
- The stimulus may be an argument, explanation, principle, or brief disagreement.
- Use one of these subtypes only:
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
- Provide exactly five answer choices and exactly one correct label.
- Use standard best-answer wording: more than one choice may seem plausible, but exactly one must answer the question best.

2. reading_comprehension
- Use subtype single_passage or comparative_passages only.
- For single_passage, provide exactly one passage.
- For comparative_passages, provide exactly two related passages with distinct viewpoints, emphases, or methods.
- Passage sets should use dense but readable prose similar to legal-academic reading.
- Single passages should usually be 150-260 words.
- Comparative sets should usually use two passages of 90-170 words each.
- Provide exactly five answer choices and exactly one correct label.
- Questions may test main point, structure, function, inference, author attitude, application, principle, or the effect of new information.

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
      "similarity_controls": {
        "new_topic": true,
        "new_wording": true,
        "new_answer_choices": true,
        "no_seed_named_entities": true,
        "no_seed_numbers_or_examples": true
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
