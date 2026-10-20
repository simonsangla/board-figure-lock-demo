"""./demo: the one command a stranger runs. Checks the key lines the README promises, and that a failed step
is never hidden behind a green exit code (each failure case runs on a broken copy of the repo)."""
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = ["demo", "bin", "board-figure-lock"]


def run(root, *args):
    return subprocess.run(["sh", os.path.join(root, "demo"), *args], capture_output=True, text=True, cwd="/")


class TestDemo(unittest.TestCase):
    def broken_copy(self, rel, old, new):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        for p in PARTS:
            src = os.path.join(ROOT, p)
            (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(tmp, p))
        path = os.path.join(tmp, rel)
        with open(path) as f:
            s = f.read()
        self.assertIn(old, s)
        with open(path, "w") as f:
            f.write(s.replace(old, new))
        return tmp

    def test_runs_and_shows_reconcile_scores_and_tableau(self):
        p = run(ROOT, "--db", "sqlite")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout
        for fig in ("BF01", "BF02", "BF04"):
            self.assertRegex(out, fig + r" .*\| OK ")
        self.assertEqual(out.count("| GAP "), 1)
        self.assertRegex(out, r"BF03 .*\| GAP ")
        self.assertRegex(out, r"BF05 .*\| REFUSED ")
        self.assertRegex(out, r"qwen2.5-coder-7b +\| answers 35 \| correct \(released \+ refused\) 25 \| blocked +0")
        self.assertRegex(out, r"semantic-layer +\| answers +7 \| correct \(released \+ refused\) +5")
        self.assertRegex(out, r"control-wrong +\| answers +4 \| correct \(released \+ refused\) +1 \| blocked +3")
        self.assertRegex(out, r"revenue\t.*\tMATCH")

    def test_bad_option_fails(self):
        self.assertNotEqual(run(ROOT, "--db", "nosuchengine").returncode, 0)

    def test_a_second_gap_fails(self):
        root = self.broken_copy("board-figure-lock/data/board_figures.csv", "BF02,2026-02-01,2026-02-28,revenue,19396.50",
                                "BF02,2026-02-01,2026-02-28,revenue,19000.00")
        self.assertNotEqual(run(root, "--db", "sqlite").returncode, 0)

    def test_a_reconcile_crash_fails(self):
        root = self.broken_copy("board-figure-lock/data/metrics.json", "{", "{{")
        self.assertNotEqual(run(root, "--db", "sqlite").returncode, 0)

    def test_a_score_failure_fails(self):
        root = self.broken_copy("board-figure-lock/answers/control-wrong.csv", "net promoter score", "no such question")
        self.assertNotEqual(run(root, "--db", "sqlite").returncode, 0)

    def test_a_tableau_mismatch_fails(self):
        root = self.broken_copy("board-figure-lock/tableau/map.json", '"calculation": "Revenue"', '"calculation": "Nope"')
        self.assertNotEqual(run(root, "--db", "sqlite").returncode, 0)


if __name__ == "__main__":
    unittest.main()
