You are answering one GRE-style Verbal Reasoning item.

Rules:
- Use only the provided passage, stem, and answer choices.
- Do not explain your reasoning.
- Return only valid JSON. No markdown, no commentary.
- For each answer group, return the blank value exactly as shown in the item: null, 1, 2, or 3.
- For select-one and text-completion blanks, return exactly one label.
- For sentence-equivalence items, return exactly two labels.
- For select-one-or-more items, return every label that is correct.

Return JSON with this schema:
{
  "answers": [
    {
      "blank": null,
      "labels": ["A"]
    }
  ]
}

Item:
{{ITEM_JSON}}
