You are an expert cognitive assessment designer, quantitative reasoning specialist, and psychometrician with experience designing elite trading firm (e.g., Optiver, Jane Street) cognitive tests.

Your task is to generate a high-quality synthetic dataset of **Optiver-level cognitive assessment problems**, formatted as a **full-length multi-section test**.

---

## OBJECTIVE

Create a dataset that evaluates:

1. Rapid quantitative reasoning
2. Multi-step logical reasoning
3. Planning and strategy
4. Probabilistic thinking under uncertainty
5. Attention and noise robustness
6. Pattern recognition under time pressure

The dataset must reflect **elite-level difficulty**, comparable to top quant trading assessments.

---

## CRITICAL CONSTRAINTS (STRICT)

* Generate EXACTLY **60 problems**
* ALL problems must be **HARD or VERY HARD**
* ABSOLUTELY NO easy or medium questions
* Avoid textbook-style or standard exam questions
* Avoid direct formula application
* Avoid single-step reasoning
* Every problem must require **multi-step reasoning or insight**
* Problems should feel like **real trading cognitive tests under time pressure**

---

## TEST STRUCTURE (VERY IMPORTANT)

Divide the dataset into:

### 6 SECTIONS (like real assessments)

* Each section has EXACTLY **10 questions**
* Each section must be a **MIXED BAG**:

  * mental math
  * probability
  * logic
  * planning
  * pattern recognition
  * attention/distractor

👉 DO NOT group by category
👉 Each section should feel like a real timed test

---

## DATASET SCHEMA (INTERNAL)

Generate full dataset internally in JSON format:

{
"dataset_name": "Optiver_Level_Cognitive_Benchmark_v3",
"sections": [
{
"section_id": "Section_1",
"problems": [...]
}
]
}

Each problem must include:

* id
* category
* difficulty
* skills_tested
* problem
* options (A–E when applicable)
* answer
* solution
* reasoning_steps
* cognitive_load
* noise_injected

---

## PDF OUTPUT REQUIREMENTS (CRITICAL)

Export the dataset into **6 separate PDFs**:

### PDF FORMAT RULES

For EACH section:

* One PDF per section
* Title: "Optiver Cognitive Assessment – Section X"
* Include ONLY:

  * Question number (1–10)
  * Problem statement
  * Answer options (A–E)

### DO NOT INCLUDE:

* Answers
* Solutions
* Hints

---

## ANSWER KEY (SEPARATE OUTPUT)

After generating PDFs, also provide:

A separate structured answer key:

{
"Section_1": {
"Q1": "B",
...
}
}

---

## DIFFICULTY ENFORCEMENT

HARD:

* Minimum 3–4 reasoning steps

VERY HARD:

* Minimum 5–8 reasoning steps
* Must include insight or deceptive structure

---

## ADVANCED REQUIREMENTS

1. TRAP DESIGN

   * Include realistic wrong answers based on:

     * cognitive biases
     * partial reasoning

2. NOISE INJECTION

   * At least 30% problems must include:

     * irrelevant numbers
     * misleading conditions

3. DIVERSITY

   * No repeated templates
   * No predictable patterns

4. REALISM

   * Questions must feel like actual trading firm tests

---

## QUALITY FILTER (MANDATORY)

Reject any problem that:

* Can be solved in < 2 steps
* Is purely computational
* Feels like a standard exam problem
* Lacks a reasoning twist

---

## FINAL INSTRUCTION

Before generating:

* Calibrate to **top 1% cognitive difficulty**
* Think like a quant trading firm test designer
* Prioritize depth, trickiness, and reasoning complexity

Then:

1. Generate full dataset
2. Convert into **6 PDFs (one per section)**
3. Provide **separate answer key JSON**