"""Board Figure Lock gate: known-good passes, wrong figure fails, undefined metric refused.
Runs on sqlite3 (stdlib, always) and on DuckDB when it is importable (no install in bin/check)."""
import importlib.machinery
import importlib.util
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BFL = os.path.join(ROOT, "bin", "bfl")
ANS = os.path.join(ROOT, "board-figure-lock", "answers")

loader = importlib.machinery.SourceFileLoader("bfl", BFL)
bfl = importlib.util.module_from_spec(importlib.util.spec_from_loader("bfl", loader))
loader.exec_module(bfl)

DBS = ["sqlite"] + (["duckdb"] if importlib.util.find_spec("duckdb") else [])


class TestGate(unittest.TestCase):
    def setUp(self):
        self.qs = {q["question"]: q for q in bfl.load("questions.csv")}
        self.figs, self.mets = bfl.figures(), bfl.metrics()

    def verdict(self, con, q, decision, sql, disputed=None):
        return bfl.gate(con, self.qs[q], decision, sql, self.figs, self.mets, disputed)[0]

    def test_reconcile_finds_the_deliberate_gap_and_refuses_units(self):
        for db in DBS:
            with self.subTest(db=db):
                con, _ = bfl.connect(db)
                self.addCleanup(con.close)
                got = {r[0]: r[4] for r in bfl.reconcile(con)}
                self.assertEqual(got, {"BF01": "OK", "BF02": "OK", "BF03": "GAP", "BF04": "OK", "BF05": "REFUSED"})

    def test_known_good_passes_wrong_fails_undefined_refused(self):
        for db in DBS:
            with self.subTest(db=db):
                con, _ = bfl.connect(db)
                self.addCleanup(con.close)
                good = "SELECT SUM(actual_revenue) FROM fct_monthly_revenue"
                self.assertEqual(self.verdict(con, "total revenue", "SQL", good), "RELEASED")
                self.assertEqual(self.verdict(con, "total revenue", "SQL", "SELECT SUM(quantity * unit_price) FROM orders"), "BLOCKED")
                self.assertEqual(self.verdict(con, "net promoter score", "DECLINE", "DECLINE"), "REFUSED")
                self.assertEqual(self.verdict(con, "churn rate by month", "SQL", "SELECT 0.05"), "BLOCKED")
                self.assertEqual(self.verdict(con, "total revenue", "DECLINE", "DECLINE"), "MISSED")
                self.assertEqual(self.verdict(con, "total revenue", "SQL", "SELECT nope FROM missing"), "BLOCKED")

    def test_disputed_board_figure_is_never_released(self):
        con, _ = bfl.connect("sqlite")
        self.addCleanup(con.close)
        by_month = "SELECT order_month, SUM(actual_revenue) FROM fct_monthly_revenue GROUP BY 1"
        self.assertEqual(self.verdict(con, "revenue by month", "SQL", by_month), "BLOCKED")
        self.assertEqual(self.verdict(con, "revenue by month", "SQL", by_month, {"BF03": 17596.10}), "HOLD")
        board = "SELECT * FROM (VALUES ('2026-01-01', 16553.70), ('2026-02-01', 19396.50), ('2026-03-01', 17600.00))"
        self.assertEqual(self.verdict(con, "revenue by month", "SQL", board), "RELEASED")
        self.assertEqual(self.verdict(con, "revenue by month", "SQL", board, {"BF03": 17596.10}), "HOLD")
        dup = board[:-1] + ", ('2026-03-01', 17600.00))"
        self.assertEqual(self.verdict(con, "revenue by month", "SQL", dup), "BLOCKED")

    def test_semantic_answers_match_committed_file(self):
        r = subprocess.run([BFL, "answer"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(ANS, "semantic-layer.csv")) as f:
            self.assertEqual(r.stdout, f.read())

    def test_score_two_engines_same_on_every_db(self):
        files = [os.path.join(ANS, f) for f in ("qwen2.5-coder-7b.csv", "semantic-layer.csv", "control-wrong.csv")]
        outs = []
        for db in DBS:
            r = subprocess.run([BFL, "--db", db, "score"] + files, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.split("\n", 1)[1])
        score = outs[0].split("== Score\n")[1]
        self.assertIn("qwen2.5-coder-7b   | answers 35 | correct (released + refused) 25 | blocked  0", score)
        self.assertIn("semantic-layer     | answers  7 | correct (released + refused)  5 | blocked  0", score)
        self.assertIn("control-wrong      | answers  4 | correct (released + refused)  1 | blocked  3", score)
        self.assertEqual(len(set(outs)), 1, "verdicts differ between local engines")

    def test_no_snowflake_anywhere_in_the_tool(self):
        with open(BFL) as f:
            src = f.read().lower()
        self.assertNotIn("import snowflake", src)
        self.assertNotIn("snowflake.connector", src)


if __name__ == "__main__":
    unittest.main()
