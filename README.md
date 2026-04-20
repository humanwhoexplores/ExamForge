# GRE Verbal Synthetic Dataset with Distilabel

This workspace contains a practical Distilabel pipeline for generating GRE-style Verbal Reasoning questions from seed examples.

Important: if you use official ETS/GRE questions as seeds, keep them private. Do not publish the seed file, and do not ask the model to paraphrase the original question. The prompt in this repo asks the model to preserve the tested skill and format while changing topic, wording, names, numbers, answer choices, and explanation.

## What It Generates

The output JSONL format supports the three GRE Verbal Reasoning families:

- `text_completion`
- `sentence_equivalence`
- `reading_comprehension`

Each generated item includes:

- question stem and optional passage
- answer choice groups
- correct answer labels
- explanation
- difficulty
- skill tags
- source seed ID and generator model metadata

## Install

Distilabel is not currently installed in this workspace. Create an environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your provider key. For OpenAI-compatible generation:

```bash
export OPENAI_API_KEY="your-key"
```

## Prepare Seed Data

Copy the example file and replace the invented examples with your private seed records:

```bash
cp data/seed_questions.example.jsonl data/seed_questions.jsonl
```

Each line should be one JSON object. Minimum useful fields:

```json
{
  "seed_id": "tc-001",
  "question_type": "text_completion",
  "source_question": "Private seed question text here.",
  "source_answer": "C",
  "source_explanation": "Why the answer is correct.",
  "skill_tags": ["contrast", "vocabulary-in-context"],
  "difficulty": 3
}
```

## Generate Dataset

Run a small first pass:

```bash
python src/generate_gre_verbal.py \
  --input data/seed_questions.jsonl \
  --output data/generated_gre_verbal.jsonl \
  --raw-output data/raw_generations.jsonl \
  --model "$OPENAI_MODEL" \
  --items-per-seed 2
```

If `OPENAI_MODEL` is not set, the script uses `gpt-4o-mini` as a configurable default. You can replace it with any OpenAI-compatible model name available in your account.

Validate the resulting JSONL:

```bash
python src/validate_dataset.py data/generated_gre_verbal.jsonl
```

Optionally run an LLM-as-judge pass. This is recommended before using the questions as a benchmark:

```bash
python src/judge_gre_verbal.py \
  --input data/generated_gre_verbal.jsonl \
  --seeds data/seed_questions.jsonl \
  --accepted-output data/accepted_gre_verbal.jsonl \
  --reviewed-output data/reviewed_gre_verbal.jsonl \
  --model "$OPENAI_JUDGE_MODEL"
```

If `OPENAI_JUDGE_MODEL` is not set, the judge falls back to `OPENAI_MODEL`, then `gpt-4o`.

## Recommended Workflow

1. Use 20-50 seed questions per question type for the first run.
2. Generate 2-4 variants per seed.
3. Validate JSON structure.
4. Run the LLM judge to filter format errors, bad answer keys, weak distractors, and seed leakage.
5. Manually review a sample for ambiguity and answer quality.
6. Freeze the benchmark set before testing other LLMs.

## Sources Checked

- Distilabel current docs describe pipelines as DAGs built from Steps, Tasks, and LLMs, with `Pipeline.run()` returning a Distiset.
- Distilabel `TextGeneration` takes dynamic input columns, defaults to `instruction`, and outputs `generation` plus `model_name`.
- ETS describes GRE Verbal Reasoning as Reading Comprehension, Text Completion, and Sentence Equivalence.
