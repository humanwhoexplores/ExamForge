# GRE Verbal Synthetic Dataset with Distilabel

This workspace contains a practical Distilabel pipeline for generating GRE-style Verbal Reasoning questions from seed examples.

Important: if you use official ETS/GRE questions as seeds, keep them private. Do not publish the seed file, and do not ask the model to paraphrase the original question. The prompt in this repo asks the model to preserve the tested skill and format while changing topic, wording, names, numbers, answer choices, and explanation.

The repo now also includes a current-format LSAT prompt pack for `logical_reasoning` and `reading_comprehension`. Those prompts are designed for the post-August-2024 multiple-choice LSAT format and can be used with the same scripts by passing `--prompt`.

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

For LSAT prompts, the generated schema uses:

- `logical_reasoning` items with a short `stimulus`
- `reading_comprehension` items with `passage_set_id` and a `passages` array
- the same `answer_groups` structure used elsewhere in this repo, so solver grading still works

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

For LSAT prompt runs, start from `data/lsat_seed_questions.example.jsonl`. The existing generator, judge, solver, and novelty scripts can be reused by passing the LSAT prompt files explicitly.

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

## Score Novelty and Hardness

There is no universal metric that proves a generated question is "X% different" from a source question. This repo uses a practical novelty score from several signals: lexical overlap, phrase overlap, answer-choice reuse, distinctive entity/number reuse, and sentence-structure similarity. Treat this as an engineering filter, not a legal originality guarantee.

Score generated or judged items against your private seeds. You can add more files to `--sources` when you also have sample sets you want to avoid resembling:

```bash
python src/score_gre_novelty.py \
  --input data/reviewed_gre_verbal.jsonl \
  --sources data/seed_questions.jsonl \
  --output data/novelty_scored_gre_verbal.jsonl \
  --summary-output data/novelty_summary.json \
  --threshold 75
```

Each output row gets `novelty_score`, `max_similarity_source_id`, `novelty_components`, `novelty_pass`, and gate reasons. By default, an item fails if its score is below 75, if it reuses a distinctive entity or number, or if it copies an answer choice.

To measure whether baseline LLMs solve the questions, run the solver benchmark. The prompt hides the answer key and explanation, then exact-match grades the returned labels:

```bash
python src/solve_gre_verbal.py \
  --input data/novelty_scored_gre_verbal.jsonl \
  --output data/solved_gre_verbal.jsonl \
  --summary-output data/solver_summary.json \
  --models gpt-4o-mini gpt-4o
```

For offline tests or prior model outputs, provide response rows instead of calling an LLM:

```json
{"item_id":"tc-001","model":"mock-llm","generation":"{\"answers\":[{\"blank\":1,\"labels\":[\"A\"]}]}"}
```

```bash
python src/solve_gre_verbal.py \
  --input data/novelty_scored_gre_verbal.jsonl \
  --responses data/mock_solver_responses.jsonl \
  --output data/solved_gre_verbal.jsonl
```

Finally, filter and rank the valid items. The default target is an accepted set with solver accuracy at or below 85%; the summary reports whether that target was met.

```bash
python src/filter_gre_verbal.py \
  --input data/solved_gre_verbal.jsonl \
  --output data/accepted_gre_verbal.jsonl \
  --rejected-output data/rejected_gre_verbal.jsonl \
  --summary-output data/filter_summary.json \
  --target-size 50 \
  --min-novelty 75 \
  --max-dataset-solver-accuracy 0.85
```

Use `--enforce-solver-target` if you want the filter to drop the easiest accepted items until the accepted set meets the solver-accuracy target.

For a harder fair-generation pass, use `prompts/gre_verbal_hard_synthetic_prompt.md` with the existing generator:

```bash
python src/generate_gre_verbal.py \
  --input data/seed_questions.jsonl \
  --output data/generated_hard_gre_verbal.jsonl \
  --prompt prompts/gre_verbal_hard_synthetic_prompt.md \
  --items-per-seed 4 \
  --temperature 0.9
```

For current-format LSAT generation, use the parallel LSAT prompts:

```bash
python src/generate_gre_verbal.py \
  --input data/lsat_seed_questions.example.jsonl \
  --output data/generated_lsat.jsonl \
  --prompt prompts/lsat_synthetic_prompt.md \
  --items-per-seed 2
```

For a harder LSAT benchmark pass:

```bash
python src/generate_gre_verbal.py \
  --input data/lsat_seed_questions.example.jsonl \
  --output data/generated_hard_lsat.jsonl \
  --prompt prompts/lsat_hard_synthetic_prompt.md \
  --items-per-seed 4 \
  --temperature 0.9
```

The validator now accepts:

- GRE `text_completion`, `sentence_equivalence`, and legacy `reading_comprehension`
- LSAT `logical_reasoning`
- LSAT `reading_comprehension` with `single_passage` or `comparative_passages`

## Recommended Workflow

1. Use 20-50 seed questions per question type for the first run.
2. Generate 2-4 variants per seed, or more when building a hard benchmark.
3. Validate JSON structure.
4. Run the LLM judge to filter format errors, bad answer keys, weak distractors, and seed leakage.
5. Run novelty scoring against seed/sample questions.
6. Run the solver benchmark against one or more baseline LLMs.
7. Filter by judge validity, novelty, and measured solver difficulty.
8. Manually review a sample for ambiguity and answer quality.
9. Freeze the benchmark set before testing other LLMs.

## Sources Checked

- Distilabel current docs describe pipelines as DAGs built from Steps, Tasks, and LLMs, with `Pipeline.run()` returning a Distiset.
- Distilabel `TextGeneration` takes dynamic input columns, defaults to `instruction`, and outputs `generation` plus `model_name`.
- ETS describes GRE Verbal Reasoning as Reading Comprehension, Text Completion, and Sentence Equivalence.
