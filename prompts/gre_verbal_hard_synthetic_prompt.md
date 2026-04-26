You are generating a benchmark dataset of fair but difficult GRE-style Verbal Reasoning questions.

Generate exactly {{ITEMS_PER_SEED}} new questions from the seed record below.

Goal:
- Create questions that remain unambiguous and GRE-style, but are difficult for strong language models because they require precise reasoning rather than surface pattern matching.
- Preserve only the abstract tested skill, difficulty band, and question format.
- Do not copy or lightly paraphrase the seed.

Hard constraints:
- Do not reuse distinctive sentences, named entities, numbers, examples, scenarios, or answer choices from the seed.
- Every generated question must have one unambiguously correct answer set.
- Every correct answer must be fully supported by the stem or passage.
- Distractors must be plausible, grammatically compatible, and wrong for precise reasons.
- Do not rely on trivia, obscure facts, archaic vocabulary, misleading formatting, or ambiguity.
- Do not mention GRE, ETS, or the seed question in generated items.
- Return only valid JSON. No markdown, no commentary.

Difficulty design:
- Reading comprehension should use dense but clear academic prose with qualification, competing interpretations, methodological limits, inference, function, weakening, or author's-attitude reasoning.
- Reading comprehension distractors should often reuse real passage language while making a subtly unsupported, reversed, overstated, or scope-shifted claim.
- Text completion should emphasize multi-blank logic, negation, concession, "less X than Y" structures, and contextually tempting but wrong vocabulary.
- Sentence equivalence should include plausible synonym pairs that fail the sentence logic, while exactly two choices both fit the sentence and produce similar completed meanings.
- Avoid questions that can be solved by matching a single obvious clue word.

Question-type requirements:

1. text_completion
- Use 1 to 3 blanks.
- One-blank items should have five choices.
- Two-blank or three-blank items should have three choices per blank.
- Each blank has exactly one correct answer.

2. sentence_equivalence
- Use exactly one sentence with one blank.
- Provide exactly six choices.
- Exactly two choices must complete the sentence coherently and produce equivalent meanings.

3. reading_comprehension
- Write a fresh passage, normally 100-190 words unless the seed clearly implies a shorter item.
- Provide a question testing inference, main idea, function, author's attitude, strengthening/weakening, or vocabulary in context.
- Provide five answer choices unless the seed specifies a select-one-or-more format.

JSON schema to return:
{
  "items": [
    {
      "question_type": "text_completion | sentence_equivalence | reading_comprehension",
      "subtype": "one_blank | two_blank | three_blank | select_one | select_one_or_more | select_sentence",
      "difficulty": 1,
      "skill_tags": ["tag-1", "tag-2"],
      "passage": null,
      "stem": "Question text. Use [blank_1], [blank_2], etc. for blanks.",
      "answer_groups": [
        {
          "blank": 1,
          "choices": [
            {"label": "A", "text": "choice text"}
          ],
          "correct_labels": ["A"]
        }
      ],
      "explanation": "Concise explanation of why the correct answer is right and why the strongest distractors are wrong.",
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
        "no_seed_numbers_or_examples": true
      }
    }
  ]
}

Seed record:
{{SEED_JSON}}
