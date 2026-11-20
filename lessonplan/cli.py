"""命令行入口：教案文本转 A4 可打印教案。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import LessonPlan, LessonplanError, load_plan, total_chars
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lessonplan",
        description="教案模板：分节文本一键生成 A4 可打印教案",
    )
    parser.add_argument("--version", action="version", version="lessonplan 0.1.0")
    parser.add_argument(
        "-i", "--input", required=True, help="教案文本文件（课题：… 分节书写）"
    )
    parser.add_argument(
        "-o", "--output", default="教案.html", help="输出 HTML 路径"
    )
    parser.add_argument("--title", default=None, help="覆盖教案标题")
    parser.add_argument("--teacher", default="", help="执教老师")
    parser.add_argument("--date", default="", help="日期，例如 2026-11-21")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        plan: LessonPlan = load_plan(args.input)
        page = render_html(
            plan,
            title=args.title,
            teacher=args.teacher,
            date=args.date,
        )
    except LessonplanError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取教案失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：课题「%s」，%d 个小节，共 %d 字"
        % (args.output, plan.title, len(plan.sections), total_chars(plan))
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
