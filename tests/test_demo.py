"""./demo: the one command a stranger runs. Checks the key lines the README promises, and that a failed step
is not hidden behind a green exit code."""
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run(["sh", os.path.join(ROOT, "demo"), *args], capture_output=True, text=True, cwd="/")


class TestDemo(unittest.TestCase):
    def test_runs_and_shows_reconcile_scores_and_tableau(self):
        p = run("--db", "sqlite")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout
        self.assertRegex(out, r"BF03 .*\| GAP ")
        self.assertRegex(out, r"BF05 .*\| REFUSED ")
        self.assertIn("qwen2.5-coder-7b   | answers 35 | correct (released + refused) 25 | blocked  0", out)
        self.assertIn("semantic-layer     | answers  7 | correct (released + refused)  5", out)
        self.assertIn("control-wrong      | answers  4 | correct (released + refused)  1 | blocked  3", out)
        self.assertRegex(out, r"revenue\t.*\tMATCH")

    def test_a_failing_step_fails_the_demo(self):
        self.assertNotEqual(run("--db", "nosuchengine").returncode, 0)


if __name__ == "__main__":
    unittest.main()
