You are an expert LSAT item writer for the current multiple-choice exam format.

You will receive two attached PDFs:
1. A current-format LSAT-style practice set with solutions.
2. A rubric describing current LSAT Logical Reasoning and Reading Comprehension skills.

Your task is to study both PDFs and generate exactly 30 new, original LSAT-style multiple-choice questions.

Before writing the output, silently analyze:
- the practice set's question formats, difficulty, wording style, answer-choice style, and explanation style
- the rubric's description of what current LSAT Logical Reasoning and Reading Comprehension test
- common reasoning patterns such as strengthening, weakening, necessary assumption, flaw, inference, principle application, method of reasoning, main point, structure, author attitude, comparison, and effect of new information
- LSAT-style distractors: plausible, textually grounded, and wrong for a precise reason

Do not output your analysis. Output only the final JSONL.

Originality requirements:
- Do not copy, lightly paraphrase, summarize, or transform any source question, stimulus, passage, answer choice, explanation, named entity, distinctive example, numerical detail, or scenario from the PDFs.
- Preserve only abstract skills, formats, and difficulty patterns.
- Use fresh topics, passages, examples, and answer choices.
- Do not mention LSAT, LSAC, the PDFs, the rubric, or the source practice set inside any generated question, stimulus, passage, answer choice, explanation, or metadata field.
- Every generated question must have exactly one best answer.
- Every correct answer must be fully supported by the stimulus or passage set.
- Use difficult but fair reasoning. Avoid trivia, outside knowledge, formal-logic notation, and gimmicks that create ambiguity.

Output format:
- Output exactly 30 JSONL records.
- Each line must be one valid JSON object.
- Do not output markdown fences, headings, comments, bullets, blank lines, or explanatory text outside the JSONL.
- Use double quotes for all JSON strings.
- Use null for fields that do not apply.

Question distribution:
- Exactly 20 logical_reasoning questions.
- Exactly 10 reading_comprehension questions.

Logical Reasoning distribution:
- Use these exact subtype counts:
  - 4 strengthen
  - 4 weaken
  - 3 necessary_assumption
  - 3 flaw
  - 2 inference
  - 2 principle
  - 2 method_of_reasoning
- Each logical_reasoning item must have:
  - one short stimulus
  - one answer group with blank null
  - exactly five answer choices
  - exactly one correct label

Reading Comprehension distribution:
- Create exactly 2 original passage sets with 5 questions each.
- Use passage_set_id values "rc-set-01" and "rc-set-02".
- "rc-set-01" must be subtype "single_passage" and use exactly one passage object.
- "rc-set-02" must be subtype "comparative_passages" and use exactly two passage objects.
- Every question in the same set must repeat the exact same passages array and passage_set_id.
- Each reading_comprehension item must have:
  - one answer group with blank null
  - exactly five answer choices
  - exactly one correct label

Reading Comprehension mix:
- rc-set-01 must include one question each targeting:
  - main point or primary purpose
  - structure or function
  - inference
  - author attitude
  - application of a principle or effect of new information
- rc-set-02 must include one question each targeting:
  - relationship between the passages
  - key difference in viewpoint or emphasis
  - inference from one or both passages
  - author attitude or rhetorical role
  - application, analogy, or effect of new information across the pair

Required schema for every JSONL record:
{
  "id": "string",
  "question_type": "logical_reasoning | reading_comprehension",
  "subtype": "strengthen | weaken | necessary_assumption | flaw | inference | principle | method_of_reasoning | single_passage | comparative_passages",
  "difficulty": 1,
  "skill_tags": ["string"],
  "stimulus": "string or null",
  "passage_set_id": "string or null",
  "passages": [
    {"label": "A", "text": "string"}
  ],
  "stem": "string",
  "answer_groups": [
    {
      "blank": null,
      "choices": [
        {"label": "A", "text": "choice text"}
      ],
      "correct_labels": ["A"]
    }
  ],
  "explanation": "string",
  "source_basis": {
    "practice_set_pattern": "brief abstract pattern used, not source content",
    "rubric_skill": "brief LSAT reasoning skill tested"
  },
  "originality_check": {
    "new_topic": true,
    "new_wording": true,
    "new_answer_choices": true,
    "no_source_named_entities": true,
    "no_source_numbers_or_examples": true
  }
}

Field rules:
- id values must be unique and use these prefixes:
  - lr-001 through lr-020 for logical_reasoning
  - rc-001 through rc-010 for reading_comprehension
- difficulty must be an integer from 1 to 5.
- skill_tags must contain 2-5 short lowercase tags.
- For logical_reasoning, stimulus must be non-null, passage_set_id must be null, and passages must be null.
- For reading_comprehension, stimulus must be null, passage_set_id must be non-null, and passages must be a non-null array.
- explanations must be concise but complete. Explain why the correct answer is best and why the strongest distractor or distractors fail.

Quality checklist before final output:
- Exactly 30 JSONL lines.
- Exactly 20 logical_reasoning and 10 reading_comprehension records.
- Exact logical_reasoning subtype counts as specified above.
- Exactly 2 reading_comprehension passage sets of 5 questions each.
- rc-set-01 uses one passage and rc-set-02 uses two passages.
- Every answer group uses blank null, exactly five choices, and exactly one correct label.
- No copied or lightly paraphrased source material.
- Output only JSONL.
