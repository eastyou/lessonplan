"""lessonplan：分节文本生成 A4 可打印教案。"""

from __future__ import annotations

from .model import (
    MAX_BODY,
    MAX_HEADING,
    MAX_META,
    MAX_TITLE,
    META_KEYS,
    LessonPlan,
    LessonplanError,
    format_plan,
    iter_lines,
    load_plan,
    meta_items,
    parse_text,
    section_names,
    total_chars,
)
from .render import render_html

__version__ = "0.1.0"

__all__ = [
    "MAX_BODY",
    "MAX_HEADING",
    "MAX_META",
    "MAX_TITLE",
    "META_KEYS",
    "LessonPlan",
    "LessonplanError",
    "format_plan",
    "iter_lines",
    "load_plan",
    "meta_items",
    "parse_text",
    "render_html",
    "section_names",
    "total_chars",
    "__version__",
]
