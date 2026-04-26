import argparse
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from filter_gre_verbal import filter_items
from score_gre_novelty import score_item_against_sources
from solve_gre_verbal import attach_solver_results, grade_item_answer
from validate_dataset import validate_record


def text_completion_item(item_id="tc-test", stem=None, choices=None):
    return {
        "id": item_id,
        "question_type": "text_completion",
        "subtype": "one_blank",
        "difficulty": 3,
        "skill_tags": ["contrast", "vocabulary-in-context"],
        "passage": None,
        "stem": stem
        or "Although the committee admired the proposal's ambition, it rejected the plan as [blank_1] because it ignored budgetary constraints.",
        "answer_groups": [
            {
                "blank": 1,
                "choices": choices
                or [
                    {"label": "A", "text": "visionary"},
                    {"label": "B", "text": "feasible"},
                    {"label": "C", "text": "imprudent"},
                    {"label": "D", "text": "concise"},
                    {"label": "E", "text": "impartial"},
                ],
                "correct_labels": ["C"],
            }
        ],
        "explanation": "Ignoring budgetary constraints makes the plan imprudent.",
    }


def logical_reasoning_item(item_id="lr-test", subtype="weaken"):
    return {
        "id": item_id,
        "question_type": "logical_reasoning",
        "subtype": subtype,
        "difficulty": 4,
        "skill_tags": ["weaken", "causal-reasoning"],
        "stimulus": (
            "A planner argues that adding more bike racks near the train station will reduce car "
            "traffic downtown, because commuters who drive to the station will instead bike there."
        ),
        "passage_set_id": None,
        "passages": None,
        "stem": "Which one of the following, if true, most weakens the planner's argument?",
        "answer_groups": [
            {
                "blank": None,
                "choices": [
                    {"label": "A", "text": "Many commuters already use the train station on weekdays."},
                    {"label": "B", "text": "Most commuters who drive to the station live too far away to bike there."},
                    {"label": "C", "text": "The station recently added a covered waiting area."},
                    {"label": "D", "text": "Several downtown employers subsidize transit passes."},
                    {"label": "E", "text": "Some commuters prefer to arrive before sunrise."},
                ],
                "correct_labels": ["B"],
            }
        ],
        "explanation": (
            "If the target commuters live too far away to bike to the station, more bike racks are "
            "less likely to reduce downtown car traffic."
        ),
    }


def reading_comprehension_item(item_id="rc-lsat-test", comparative=False):
    passages = (
        [
            {
                "label": "A",
                "text": (
                    "Some legal historians argue that administrative guidance documents chiefly "
                    "clarify existing duties rather than create new ones. On this view, agencies use "
                    "guidance to summarize settled interpretations for regulated parties who need "
                    "predictability."
                ),
            },
            {
                "label": "B",
                "text": (
                    "Other scholars contend that guidance documents often function more expansively. "
                    "Even when formally nonbinding, such documents can influence behavior because "
                    "regulated parties anticipate how officials will exercise discretion."
                ),
            },
        ]
        if comparative
        else [
            {
                "label": "A",
                "text": (
                    "Courts sometimes describe precedent as constraining judicial discretion, yet the "
                    "constraint is rarely mechanical. A precedent may specify a rule, but later judges "
                    "still decide how broadly to read that rule, which facts matter, and whether an "
                    "apparent exception is genuine."
                ),
            }
        ]
    )
    stem = (
        "Which one of the following best describes a difference between the passages?"
        if comparative
        else "Which one of the following most accurately states the main point of the passage?"
    )
    choices = (
        [
            {"label": "A", "text": "Passage A treats guidance as always binding, while Passage B treats it as never influential."},
            {"label": "B", "text": "Passage A emphasizes clarification of existing duties, while Passage B emphasizes practical influence despite formal nonbinding status."},
            {"label": "C", "text": "Passage A rejects the value of predictability, while Passage B defends it."},
            {"label": "D", "text": "Passage A focuses on courts, while Passage B focuses on legislatures."},
            {"label": "E", "text": "Passage A argues that discretion should be eliminated, while Passage B argues that discretion should expand."},
        ]
        if comparative
        else [
            {"label": "A", "text": "Precedent eliminates judicial interpretation by fixing the exact outcome of later cases."},
            {"label": "B", "text": "Judges generally ignore precedent when a case contains unusual facts."},
            {"label": "C", "text": "Precedent constrains judges, but later interpretation still leaves room for judgment."},
            {"label": "D", "text": "Courts should replace rules with case-by-case balancing tests."},
            {"label": "E", "text": "Exceptions to precedent are more important than the rules they qualify."},
        ]
    )
    correct = "B" if comparative else "C"
    explanation = (
        "Passage A presents guidance as clarifying existing duties, while Passage B stresses its real-world influence even without formal binding force."
        if comparative
        else "The passage says precedent constrains discretion but does not make later decisions mechanical."
    )
    return {
        "id": item_id,
        "question_type": "reading_comprehension",
        "subtype": "comparative_passages" if comparative else "single_passage",
        "difficulty": 4,
        "skill_tags": ["comparison", "structure"] if comparative else ["main-point", "qualification"],
        "stimulus": None,
        "passage_set_id": "rc-set-02" if comparative else "rc-set-01",
        "passages": passages,
        "stem": stem,
        "answer_groups": [
            {
                "blank": None,
                "choices": choices,
                "correct_labels": [correct],
            }
        ],
        "explanation": explanation,
    }


class NoveltyScoringTests(unittest.TestCase):
    def setUp(self):
        self.seed = {
            "seed_id": "tc-seed",
            "question_type": "text_completion",
            "source_question": (
                "Although the committee admired the proposal's ambition, it rejected the plan as "
                "[blank_1] because it ignored budgetary constraints. Choices: A. visionary "
                "B. feasible C. imprudent D. concise E. impartial"
            ),
            "source_answer": "C",
        }

    def test_identical_question_fails_novelty_gate(self):
        scored = score_item_against_sources(text_completion_item(), [self.seed])
        self.assertLess(scored["novelty_score"], 75)
        self.assertFalse(scored["novelty_pass"])

    def test_copied_answer_choice_fails_gate(self):
        item = text_completion_item(
            item_id="tc-choice-copy",
            stem="The critic praised the book's scope, but called its policy recommendations [blank_1].",
            choices=[
                {"label": "A", "text": "imprudent"},
                {"label": "B", "text": "melodic"},
                {"label": "C", "text": "transparent"},
                {"label": "D", "text": "decorative"},
                {"label": "E", "text": "succinct"},
            ],
        )
        scored = score_item_against_sources(item, [self.seed])
        self.assertFalse(scored["novelty_pass"])
        self.assertIn("imprudent", scored["copied_answer_choices"])

    def test_fresh_question_passes_novelty_gate(self):
        item = text_completion_item(
            item_id="tc-fresh",
            stem=(
                "The archivist's catalog was not [blank_1]; every disputed attribution was "
                "paired with a dated letter or inventory record."
            ),
            choices=[
                {"label": "A", "text": "speculative"},
                {"label": "B", "text": "durable"},
                {"label": "C", "text": "ceremonial"},
                {"label": "D", "text": "regional"},
                {"label": "E", "text": "fluent"},
            ],
        )
        item["answer_groups"][0]["correct_labels"] = ["A"]
        item["explanation"] = "Documented support means the catalog was not speculative."
        scored = score_item_against_sources(item, [self.seed])
        self.assertGreaterEqual(scored["novelty_score"], 75)
        self.assertTrue(scored["novelty_pass"])

    def test_reused_entity_or_number_fails_gate(self):
        seed = {
            "seed_id": "entity-seed",
            "source_question": "In 1912, Dr. Marlow argued that the archive was incomplete. Choices: A. cautious B. ornate C. brief D. calm E. rigid",
        }
        item = text_completion_item(
            item_id="entity-copy",
            stem="Marlow's 1912 archive note was unusually [blank_1], listing every missing file.",
            choices=[
                {"label": "A", "text": "methodical"},
                {"label": "B", "text": "florid"},
                {"label": "C", "text": "irate"},
                {"label": "D", "text": "remote"},
                {"label": "E", "text": "brief"},
            ],
        )
        scored = score_item_against_sources(item, [seed])
        self.assertFalse(scored["novelty_pass"])
        self.assertTrue({"marlow", "1912"} & set(scored["reused_distinctive_terms"]))


class SolverGradingTests(unittest.TestCase):
    def test_grades_text_completion_multiblank_exact_match(self):
        item = text_completion_item()
        item["subtype"] = "two_blank"
        item["answer_groups"] = [
            {"blank": 1, "choices": [{"label": "A", "text": "cogent"}], "correct_labels": ["A"]},
            {"blank": 2, "choices": [{"label": "D", "text": "diffuse"}], "correct_labels": ["D"]},
        ]
        parsed = {"answers": [{"blank": 1, "labels": ["A"]}, {"blank": 2, "labels": ["D"]}]}
        self.assertTrue(grade_item_answer(item, parsed)["correct"])

    def test_grades_sentence_equivalence_exact_pair(self):
        item = text_completion_item(item_id="se-test")
        item["question_type"] = "sentence_equivalence"
        item["answer_groups"] = [
            {
                "blank": 1,
                "choices": [
                    {"label": "A", "text": "opaque"},
                    {"label": "B", "text": "lucid"},
                    {"label": "C", "text": "inscrutable"},
                    {"label": "D", "text": "methodical"},
                    {"label": "E", "text": "brief"},
                    {"label": "F", "text": "ornate"},
                ],
                "correct_labels": ["A", "C"],
            }
        ]
        self.assertTrue(grade_item_answer(item, {"answers": [{"blank": 1, "labels": ["C", "A"]}]} )["correct"])
        self.assertFalse(grade_item_answer(item, {"answers": [{"blank": 1, "labels": ["A"]}]} )["correct"])

    def test_grades_reading_comprehension_select_all_and_select_sentence(self):
        select_all = {
            "id": "rc-all",
            "question_type": "reading_comprehension",
            "subtype": "select_one_or_more",
            "difficulty": 4,
            "skill_tags": ["select-all", "inference"],
            "passage": "Researchers recommend pairing bird counts with soil and plant measures.",
            "stem": "Which measures are recommended? Select all that apply.",
            "answer_groups": [
                {
                    "blank": None,
                    "choices": [
                        {"label": "A", "text": "Soil measures"},
                        {"label": "B", "text": "Plant measures"},
                        {"label": "C", "text": "Ticket sales"},
                    ],
                    "correct_labels": ["A", "B"],
                }
            ],
            "explanation": "The passage names soil and plant measures.",
        }
        self.assertTrue(grade_item_answer(select_all, {"answers": [{"blank": None, "labels": ["B", "A"]}]} )["correct"])

        select_sentence = dict(select_all)
        select_sentence["id"] = "rc-sentence"
        select_sentence["subtype"] = "select_sentence"
        select_sentence["answer_groups"] = [
            {
                "blank": None,
                "choices": [
                    {"label": "A", "text": "First sentence."},
                    {"label": "B", "text": "Second sentence."},
                ],
                "correct_labels": ["B"],
            }
        ]
        self.assertTrue(grade_item_answer(select_sentence, {"answer": "B"})["correct"])

    def test_grades_lsat_logical_reasoning_and_reading_comprehension(self):
        self.assertTrue(grade_item_answer(logical_reasoning_item(), {"answer": "B"})["correct"])
        self.assertTrue(
            grade_item_answer(
                reading_comprehension_item(comparative=True),
                {"answers": [{"blank": None, "labels": ["B"]}]},
            )["correct"]
        )


class LsatValidationTests(unittest.TestCase):
    def test_validates_logical_reasoning_item(self):
        self.assertEqual(validate_record(logical_reasoning_item(), 1), [])

    def test_validates_single_passage_rc_item(self):
        self.assertEqual(validate_record(reading_comprehension_item(comparative=False), 1), [])

    def test_validates_comparative_rc_item(self):
        self.assertEqual(validate_record(reading_comprehension_item(comparative=True), 1), [])


class FilterPipelineTests(unittest.TestCase):
    def test_mocked_solver_results_feed_filter_and_rank_hardest_item(self):
        hard = text_completion_item(item_id="hard")
        easy = text_completion_item(item_id="easy")
        for item in (hard, easy):
            item["judge"] = {"valid": True, "score": 5}
            item["novelty_score"] = 92.0
            item["novelty_pass"] = True

        solved = attach_solver_results(
            [hard, easy],
            [
                {
                    "item_id": "hard",
                    "model": "mock-llm",
                    "generation": '{"answers":[{"blank":1,"labels":["A"]}]}',
                },
                {
                    "item_id": "easy",
                    "model": "mock-llm",
                    "generation": '{"answers":[{"blank":1,"labels":["C"]}]}',
                },
            ],
        )
        args = argparse.Namespace(
            min_judge_score=4.0,
            min_novelty=75.0,
            max_item_solver_accuracy=None,
            target_size=1,
            max_dataset_solver_accuracy=0.85,
            enforce_solver_target=False,
            allow_unjudged=False,
            allow_unscored=False,
            allow_unsolved=False,
        )
        accepted, rejected, summary = filter_items(solved, args)
        self.assertEqual([item["id"] for item in accepted], ["hard"])
        self.assertEqual(rejected, [])
        self.assertEqual(summary["accepted_items"], 1)
        self.assertEqual(summary["dataset_solver_accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
