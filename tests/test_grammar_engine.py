"""Tester för grammatikmotorn."""

import unittest
from grammarbuddy.grammar_engine import (
    GrammarEngine, Difficulty, ExerciseMode, GrammarAnalysis,
)


class TestGrammarEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GrammarEngine()

    def test_empty_text(self):
        result = self.engine.analyze("", Difficulty.SFI_A)
        self.assertEqual(result.score, 0)

    def test_correct_sentence(self):
        result = self.engine.analyze("Jag bor i Stockholm.", Difficulty.SFI_A)
        self.assertEqual(result.score, 100)

    def test_missing_period(self):
        result = self.engine.analyze("Jag bor i Stockholm", Difficulty.SFI_A)
        self.assertIn("skiljetecken", [e[0] for e in result.errors])

    def test_missing_capital(self):
        result = self.engine.analyze("jag bor i Stockholm.", Difficulty.SFI_A)
        self.assertIn("stor bokstav", [e[0] for e in result.errors])

    def test_talsprak_dom(self):
        result = self.engine.analyze("Dom bor i Malmö.", Difficulty.SFI_A)
        self.assertTrue(any("dom" in e[0].lower() or "dom" in e[1].lower()
                            for e in result.errors))

    def test_double_spaces(self):
        result = self.engine.analyze("Jag  bor  här.", Difficulty.SFI_A)
        self.assertIn("mellanslag", [e[0] for e in result.errors])

    def test_exercise_exists(self):
        ex = self.engine.get_exercise(Difficulty.SFI_A, ExerciseMode.SPELLING)
        self.assertIsNotNone(ex)
        self.assertIn("prompt", ex)
        self.assertIn("answer", ex)

    def test_exercise_check_correct(self):
        ex = {"prompt": "Test", "answer": "har", "hint": "test"}
        correct, feedback = self.engine.check_exercise_answer(ex, "har")
        self.assertTrue(correct)

    def test_exercise_check_wrong(self):
        ex = {"prompt": "Test", "answer": "har", "hint": "test hint"}
        correct, feedback = self.engine.check_exercise_answer(ex, "ha")
        self.assertFalse(correct)
        self.assertIn("har", feedback)

    def test_all_difficulties_have_exercises(self):
        for diff in Difficulty:
            for mode in [ExerciseMode.SPELLING, ExerciseMode.SENTENCE,
                         ExerciseMode.TENSE, ExerciseMode.WORD_ORDER]:
                ex = self.engine.get_exercise(diff, mode)
                self.assertIsNotNone(ex, f"Missing exercise: {diff}, {mode}")


if __name__ == "__main__":
    unittest.main()
