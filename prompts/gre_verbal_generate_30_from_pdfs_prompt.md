You are an expert GRE Verbal Reasoning item writer.

You will receive two attached PDFs:
1. GRE Verbal Reasoning Practice Set 1 with solutions.
2. GRE Verbal Reasoning Question Type Rubric.

Your task is to study both PDFs and generate exactly 30 new, original GRE-style Verbal Reasoning questions.

Before writing the output, silently analyze:
- the Practice Set 1 question formats, difficulty, wording style, answer-choice style, and explanation style
- the rubric's description of what GRE Verbal Reasoning tests
- common reasoning patterns such as logical contrast, causality, qualification, inference, function, vocabulary-in-context, strengthening, weakening, author's attitude, and main idea
- GRE-style distractors: plausible, grammatically compatible, and wrong for precise reasons

Do not output your analysis. Output only the final JSONL.

Originality requirements:
- Do not copy, lightly paraphrase, summarize, or transform any source question, passage, answer choice, explanation, named entity, distinctive example, numerical detail, or scenario from the PDFs.
- Preserve only abstract skills, formats, and difficulty patterns.
- Use fresh topics, passages, names, examples, and answer choices.
- Do not mention GRE, ETS, the PDFs, the rubric, or the source practice set inside any generated question, passage, answer choice, explanation, or metadata field.
- Every generated question must have one unambiguous correct answer set.
- Every correct answer must be fully supported by the question or passage.
- Use graduate-level vocabulary and reasoning, but avoid archaic, intentionally obscure, or trivia-dependent wording.

Output format:
- Output exactly 30 JSONL records.
- Each line must be one valid JSON object.
- Do not output markdown fences, headings, comments, bullets, blank lines, or explanatory text outside the JSONL.
- Use double quotes for all JSON strings.
- Use null for fields that do not apply.

Question distribution:
- 15 reading_comprehension questions.
- 9 text_completion questions.
- 6 sentence_equivalence questions.

Reading Comprehension distribution:
- Create exactly 5 original reading passages.
- Each passage must have exactly 3 questions.
- Related questions must share the same passage_id and repeat the exact same passage text.
- Use passage_id values "rc-passage-01" through "rc-passage-05".
- Use this exact subtype distribution:
  - rc-passage-01: 2 select_one questions, 1 select_one_or_more question
  - rc-passage-02: 2 select_one questions, 1 select_sentence question
  - rc-passage-03: 2 select_one questions, 1 select_one_or_more question
  - rc-passage-04: 2 select_one questions, 1 select_sentence question
  - rc-passage-05: 2 select_one questions, 1 select_one_or_more question
- Each passage should normally be 90-180 words.
- Reading passages should cover a range of academic-style topics across sciences, social sciences, arts, humanities, and everyday analytical contexts.
- Reading Comprehension select_one questions must have five answer choices and exactly one correct label.
- Reading Comprehension select_one_or_more questions must have three answer choices and one, two, or three correct labels.
- Reading Comprehension select_sentence questions must ask the test taker to identify a sentence in the passage. Represent the selectable sentences as answer choices, with labels "A", "B", "C", etc., and put the full sentence text in each choice's text field.

Text Completion requirements:
- Generate exactly 9 text_completion questions.
- Include exactly:
  - 3 one_blank items
  - 3 two_blank items
  - 3 three_blank items
- One_blank items must have one answer group with five choices.
- Two_blank and three_blank items must have one answer group per blank, with three choices per group.
- Each blank must have exactly one correct label.
- Use [blank_1], [blank_2], and [blank_3] markers in the stem.

Sentence Equivalence requirements:
- Generate exactly 6 sentence_equivalence questions.
- Each item must contain one sentence with one [blank_1].
- Each item must have one answer group with exactly six choices.
- Exactly two choices must be correct.
- The two correct choices do not need to be exact synonyms, but each must produce a coherent sentence and the two completed sentences must be alike in meaning.
- Include at least one tempting synonym pair that does not fit the sentence in some Sentence Equivalence items.

Required schema for every JSONL record:
{
  "id": "string",
  "question_type": "reading_comprehension | text_completion | sentence_equivalence",
  "subtype": "select_one | select_one_or_more | select_sentence | one_blank | two_blank | three_blank",
  "difficulty": 1,
  "skill_tags": ["string"],
  "passage_id": "string or null",
  "passage": "string or null",
  "stem": "string",
  "answer_groups": [
    {
      "blank": 1,
      "choices": [
        {"label": "A", "text": "choice text"}
      ],
      "correct_labels": ["A"]
    }
  ],
  "explanation": "string",
  "source_basis": {
    "practice_set_pattern": "brief abstract pattern used, not source content",
    "rubric_skill": "brief verbal reasoning skill tested"
  },
  "originality_check": {
    "new_topic": true,
    "new_wording": true,
    "new_passage": true,
    "new_answer_choices": true,
    "no_source_named_entities": true,
    "no_source_numbers_or_examples": true
  }
}

Field rules:
- id values must be unique and use these prefixes:
  - rc-001 through rc-015 for reading_comprehension
  - tc-001 through tc-009 for text_completion
  - se-001 through se-006 for sentence_equivalence
- difficulty must be an integer from 1 to 5.
- skill_tags must contain 2-5 short lowercase tags, such as "inference", "contrast", "function", "vocabulary-in-context", "causal-reasoning", "sentence-logic", or "synonym-pair".
- For non-Reading Comprehension items, passage_id must be null and passage must be null.
- For Reading Comprehension items, passage_id and passage must be non-null strings.
- For Reading Comprehension answer groups, use "blank": null.
- For Text Completion and Sentence Equivalence answer groups, use the numeric blank index.
- Explanations must be concise but complete. Explain why the correct answer is right and why the most tempting distractor or distractors are wrong.

Quality checklist before final output:
- Exactly 30 JSONL lines.
- Exactly 15 reading_comprehension, 9 text_completion, and 6 sentence_equivalence records.
- Exactly 10 Reading Comprehension select_one, 3 select_one_or_more, and 2 select_sentence records.
- Exactly 3 one_blank, 3 two_blank, and 3 three_blank Text Completion records.
- Every answer label listed in correct_labels appears in that answer group's choices.
- No duplicate labels within an answer group.
- No copied or lightly paraphrased source material.
- Output only JSONL.
