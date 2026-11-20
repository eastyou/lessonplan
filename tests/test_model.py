"""model 模块单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lessonplan.model import (
    KNOWN_HEADINGS,
    MAX_BODY,
    MAX_HEADING,
    MAX_TITLE,
    LessonPlan,
    LessonplanError,
    format_plan,
    load_plan,
    meta_items,
    parse_text,
    section_names,
    total_chars,
)

SAMPLE = """课题：光合作用
科目：生物
班级：初一2班
课时：1 课时

教学目标：
1. 说明光合作用的原料和产物
2. 能写出文字表达式

教学重点：
光合作用的原料、条件与产物

教学过程：
导入：播放植物生长的视频
新授：讲解叶绿体的作用

板书设计：
光合作用
原料：二氧化碳和水
"""


class ParseTextTest(unittest.TestCase):
    def test_sample(self) -> None:
        plan = parse_text(SAMPLE)
        self.assertEqual(plan.title, "光合作用")
        self.assertEqual(plan.subject, "生物")
        self.assertEqual(plan.grade, "初一2班")
        self.assertEqual(plan.periods, "1 课时")
        self.assertEqual(
            section_names(plan),
            ["教学目标", "教学重点", "教学过程", "板书设计"],
        )

    def test_body_keeps_colon_lines(self) -> None:
        plan = parse_text(SAMPLE)
        body = plan.section("教学过程")
        self.assertIn("导入：播放植物生长的视频", body)
        self.assertIn("新授：讲解叶绿体的作用", body)

    def test_multiline_body(self) -> None:
        plan = parse_text("课题：测试\n教学目标：\n第一行\n第二行\n")
        self.assertEqual(plan.section("教学目标"), "第一行\n第二行")

    def test_inline_section_content(self) -> None:
        plan = parse_text("课题：测试\n教学目标：理解概念\n并能举例\n")
        self.assertEqual(plan.section("教学目标"), "理解概念\n并能举例")

    def test_custom_section(self) -> None:
        plan = parse_text("课题：测试\n拓展：\n补充阅读\n")
        self.assertEqual(plan.section("拓展"), "补充阅读")

    def test_duplicate_section(self) -> None:
        with self.assertRaises(LessonplanError) as ctx:
            parse_text("课题：测试\n教学目标：\n内容\n教学目标：\n再次\n")
        self.assertIn("重复", str(ctx.exception))

    def test_duplicate_title(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：A\n课题：B\n教学目标：\n内容\n")

    def test_content_before_section(self) -> None:
        with self.assertRaises(LessonplanError) as ctx:
            parse_text("这一行没有小节\n课题：测试\n教学目标：\n内容\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_missing_title(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("教学目标：\n内容\n")

    def test_empty_title(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：\n教学目标：\n内容\n")

    def test_empty_section(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：测试\n教学目标：\n")

    def test_blank_section_lines(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：测试\n教学目标：\n\n\n")

    def test_title_too_long(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：%s\n教学目标：\n内容\n" % ("字" * (MAX_TITLE + 1)))

    def test_heading_too_long(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：测试\n%s：\n内容\n" % ("字" * (MAX_HEADING + 2)))

    def test_body_too_long(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("课题：测试\n教学目标：\n%s\n" % ("字" * (MAX_BODY + 1)))

    def test_empty_text(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text("")

    def test_non_text(self) -> None:
        with self.assertRaises(LessonplanError):
            parse_text(123)  # type: ignore[arg-type]

    def test_bom(self) -> None:
        plan = parse_text("\ufeff课题：测试\n教学目标：\n内容\n")
        self.assertEqual(plan.title, "测试")

    def test_known_headings(self) -> None:
        self.assertIn("教学过程", KNOWN_HEADINGS)
        self.assertIn("教学反思", KNOWN_HEADINGS)


class LoadPlanTest(unittest.TestCase):
    def test_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.txt"
            path.write_text(SAMPLE, encoding="utf-8")
            self.assertEqual(load_plan(path).title, "光合作用")

    def test_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.txt"
            path.write_bytes(SAMPLE.encode("gbk"))
            self.assertEqual(load_plan(path).subject, "生物")

    def test_unknown_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.txt"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(LessonplanError):
                load_plan(path)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_plan("/tmp/definitely-missing-lessonplan.txt")


class LessonPlanTest(unittest.TestCase):
    def test_empty_title(self) -> None:
        with self.assertRaises(LessonplanError):
            LessonPlan(title=" ", sections=(("教学目标", "内容"),))

    def test_empty_sections(self) -> None:
        with self.assertRaises(LessonplanError):
            LessonPlan(title="测试")

    def test_empty_heading(self) -> None:
        with self.assertRaises(LessonplanError):
            LessonPlan(title="测试", sections=(("", "内容"),))

    def test_empty_body(self) -> None:
        with self.assertRaises(LessonplanError):
            LessonPlan(title="测试", sections=(("教学目标", " "),))

    def test_non_text(self) -> None:
        with self.assertRaises(LessonplanError):
            LessonPlan(title=1, sections=(("教学目标", "内容"),))  # type: ignore[arg-type]

    def test_section_lookup(self) -> None:
        plan = LessonPlan(title="测试", sections=(("教学目标", "内容"),))
        self.assertEqual(plan.section("教学目标"), "内容")
        self.assertEqual(plan.section("不存在"), "")

    def test_meta_items(self) -> None:
        plan = parse_text(SAMPLE)
        labels = [label for label, _ in meta_items(plan)]
        self.assertEqual(labels, ["科目", "班级", "课时"])

    def test_total_chars(self) -> None:
        plan = parse_text("课题：测试\n教学目标：\n四字\n")
        self.assertEqual(total_chars(plan), 2)

    def test_format_roundtrip(self) -> None:
        plan = parse_text(SAMPLE)
        again = parse_text(format_plan(plan))
        self.assertEqual(again.title, plan.title)
        self.assertEqual(again.subject, plan.subject)
        self.assertEqual(again.sections, plan.sections)

    def test_format_non_plan(self) -> None:
        with self.assertRaises(LessonplanError):
            format_plan("plan")  # type: ignore[arg-type]

    def test_section_names_non_plan(self) -> None:
        with self.assertRaises(LessonplanError):
            section_names("plan")  # type: ignore[arg-type]

    def test_total_chars_non_plan(self) -> None:
        with self.assertRaises(LessonplanError):
            total_chars("plan")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
