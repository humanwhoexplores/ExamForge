You are generating a benchmark dataset of GRE-style Verbal Reasoning questions.

Generate exactly {{ITEMS_PER_SEED}} new questions from the seed record below.

Hard constraints:
- Do not copy or lightly paraphrase the seed question.
- Do not reuse distinctive sentences, named entities, numbers, examples, or answer choices from the seed.
- Preserve only the abstract tested skill, difficulty, and question format.
- Every generated question must have one unambiguously correct answer set.
- Distractors must be plausible but wrong for a precise reason.
- Use graduate-level vocabulary and reasoning, but avoid archaic or intentionally obscure words.
- Do not mention GRE, ETS, or the seed question in the generated items.
- Return only valid JSON. No markdown, no commentary.

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
- Write a fresh passage, normally 90-180 words unless the seed clearly implies a shorter item.
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
      "explanation": "Concise explanation of why the correct answer is right and why the key distractors are wrong.",
      "similarity_controls": {
        "new_topic": true,
        "new_wording": true,
        "new_answer_choices": true,
        "no_seed_named_entities": true
      }
    }
  ]
}

Seed record:
{{SEED_JSON}}

