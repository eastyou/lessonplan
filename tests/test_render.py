"""render 模块单元测试。"""

from __future__ import annotations

import unittest

from lessonplan.model import LessonplanError, parse_text
from lessonplan.render import render_html

SAMPLE = """课题：光合作用
科目：生物
班级：初一2班
课时：1 课时

教学目标：
说明光合作用的原料和产物

教学过程：
导入：播放视频
新授：讲解叶绿体
"""


class RenderHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = parse_text(SAMPLE)

    def test_basic_document(self) -> None:
        page = render_html(self.plan)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("A4 portrait", page)
        self.assertIn("光合作用", page)

    def test_meta_line(self) -> None:
        page = render_html(self.plan)
        self.assertIn("<b>科目</b>生物", page)
        self.assertIn("<b>班级</b>初一2班", page)
        self.assertIn("<b>课时</b>1 课时", page)

    def test_teacher_and_date(self) -> None:
        page = render_html(self.plan, teacher="王老师", date="2026-11-21")
        self.assertIn("<b>执教</b>王老师", page)
        self.assertIn("<b>日期</b>2026-11-21", page)

    def test_sections(self) -> None:
        page = render_html(self.plan)
        self.assertIn("<h2>教学目标</h2>", page)
        self.assertIn("<h2>教学过程</h2>", page)
        self.assertIn("导入：播放视频", page)

    def test_section_order(self) -> None:
        page = render_html(self.plan)
        self.assertLess(page.index("教学目标"), page.index("教学过程"))

    def test_title_override(self) -> None:
        page = render_html(self.plan, title="光合作用（复习课）")
        self.assertIn("光合作用（复习课）", page)

    def test_title_escaped(self) -> None:
        page = render_html(self.plan, title="<教案>")
        self.assertIn("&lt;教案&gt;", page)

    def test_body_escaped(self) -> None:
        plan = parse_text("课题：测试\n教学目标：\n<script>alert(1)</script>\n")
        page = render_html(plan)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)

    def test_footer_chars(self) -> None:
        page = render_html(self.plan)
        self.assertIn("lessonplan", page)
        self.assertIn("2 个小节", page)

    def test_non_plan(self) -> None:
        with self.assertRaises(LessonplanError):
            render_html("plan")  # type: ignore[arg-type]

    def test_empty_title(self) -> None:
        with self.assertRaises(LessonplanError):
            render_html(self.plan, title=" ")

    def test_non_text_teacher(self) -> None:
        with self.assertRaises(LessonplanError):
            render_html(self.plan, teacher=1)  # type: ignore[arg-type]

    def test_long_teacher(self) -> None:
        with self.assertRaises(LessonplanError):
            render_html(self.plan, teacher="字" * 21)

    def test_non_text_date(self) -> None:
        with self.assertRaises(LessonplanError):
            render_html(self.plan, date=20261121)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
