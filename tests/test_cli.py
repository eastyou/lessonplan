"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List

from lessonplan.cli import main

SAMPLE = """课题：光合作用
科目：生物

教学目标：
说明光合作用的原料和产物
"""


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plan = self.root / "plan.txt"
        self.plan.write_text(SAMPLE, encoding="utf-8")
        self.target = self.root / "plan.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return main(argv)

    def test_generate(self) -> None:
        code = self.run_cli(["-i", str(self.plan), "-o", str(self.target)])
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("光合作用", page)
        self.assertIn("教学目标", page)

    def test_title_teacher_date(self) -> None:
        code = self.run_cli(
            [
                "-i", str(self.plan), "-o", str(self.target),
                "--title", "复习课", "--teacher", "王老师", "--date", "2026-11-21",
            ]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("复习课", page)
        self.assertIn("王老师", page)
        self.assertIn("2026-11-21", page)

    def test_invalid_content(self) -> None:
        bad = self.root / "bad.txt"
        bad.write_text("没有课题\n", encoding="utf-8")
        code = self.run_cli(["-i", str(bad), "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertFalse(self.target.exists())

    def test_missing_file(self) -> None:
        code = self.run_cli(
            ["-i", str(self.root / "missing.txt"), "-o", str(self.target)]
        )
        self.assertEqual(code, 1)

    def test_missing_input_argument(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["-o", str(self.target)])
        self.assertEqual(ctx.exception.code, 2)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
