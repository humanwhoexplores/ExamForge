# ExamForge

ExamForge is a Human-Centered AI project workspace for collecting, organizing, and generating exam-style assessment resources.

The repository is organized around two main resource folders:

- `data/` stores source assessments, sample datasets, answer keys, and curated question files.
- `prompts/` stores prompt templates used to generate, transform, judge, or solve assessment questions.

## `data/`

The `data/` folder contains assessment materials and dataset examples used by the project. These files may include:

- Generated question PDFs for exams or mock assessments
- answer key PDFs or JSON files

Current materials cover several assessment styles, including GRE verbal reasoning, LSAT-style reasoning, GMAT-style questions, Jane Street-style quantitative reasoning, Optiver-style cognitive assessments, and Elite Brainteasers style brainteasers.

Do not add private, copyrighted, or unreleased seed questions to this folder unless they are allowed to be shared in the repository. When private seed examples are needed, keep them outside the repo and use local copies.

## `prompts/`

The `prompts/` folder contains the prompts used to create and evaluate ExamForge datasets. These prompts document how questions were generated and make the dataset workflow easier to reproduce.

Prompt files are grouped by assessment type and task. They include:

- generation prompts for creating synthetic questions
- harder benchmark prompts for producing more difficult questions
- judge prompts for evaluating format, quality, correctness, and seed leakage
- dataset-specific prompts for LSAT, GRE verbal, GMAT, Jane Street, Optiver, and brainteaser-style question generation

When adding a new dataset or assessment style, add the prompt used to produce it under `prompts/`. Name the file clearly so it is easy to connect the prompt to the related files in `data/`.

## Suggested Workflow

1. Add or update assessment source files, samples, or answer keys in `data/`.
2. Add the prompt templates used to generate or evaluate those materials in `prompts/`.
3. Keep filenames descriptive and consistent across related question files, answer keys, and prompts.
4. Mark old resources as deprecated instead of deleting them when they are still useful for historical context.
5. Review generated questions manually before treating them as benchmark or evaluation data.

