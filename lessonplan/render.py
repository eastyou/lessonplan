"""把教案渲染成可打印的 A4 文档。"""

from __future__ import annotations

import html
from typing import List, Optional

from .model import (
    MAX_META,
    LessonPlan,
    LessonplanError,
    meta_items,
    total_chars,
)

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0


def _check_meta(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise LessonplanError("%s必须是文本" % label)
    text = value.strip()
    if len(text) > MAX_META:
        raise LessonplanError("%s最多 %d 个字符" % (label, MAX_META))
    return text


def render_html(
    plan: LessonPlan,
    title: Optional[str] = None,
    teacher: str = "",
    date: str = "",
) -> str:
    """生成完整 HTML：标题、信息行与小节正文。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    heading = plan.title if title is None else title
    if not isinstance(heading, str) or not heading.strip():
        raise LessonplanError("标题不能为空")
    heading = heading.strip()
    teacher = _check_meta(teacher, "执教老师")
    date = _check_meta(date, "日期")

    info: List[str] = []
    for label, value in meta_items(plan):
        info.append("<span><b>%s</b>%s</span>" % (label, html.escape(value)))
    if teacher:
        info.append("<span><b>执教</b>%s</span>" % html.escape(teacher))
    if date:
        info.append("<span><b>日期</b>%s</span>" % html.escape(date))

    sections: List[str] = []
    for name, body in plan.sections:
        sections.append(
            '<section class="part">'
            "<h2>%s</h2>"
            '<div class="body">%s</div>'
            "</section>" % (html.escape(name), html.escape(body))
        )

    chars = total_chars(plan)
    footer = (
        '<footer class="foot"><span>%s</span>'
        "<span>lessonplan · 共 %d 字 · %d 个小节</span></footer>"
        % (html.escape(heading), chars, len(plan.sections))
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
        '<div class="toolbar"><strong>%s</strong>'
        "<span>%s · %d 个小节 · 共 %d 字</span></div>\n"
        '<section class="sheet">'
        '<header class="head"><h1>%s</h1>'
        '<div class="info">%s</div></header>%s%s'
        "</section>\n</body>\n</html>\n"
        % (
            html.escape(heading),
            STYLE,
            html.escape(heading),
            html.escape(plan.title),
            len(plan.sections),
            chars,
            html.escape(heading),
            "".join(info),
            "".join(sections),
            footer,
        )
    )


STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto 8mm;
    padding: 17mm 20mm 14mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
  }
  .head {
    text-align: center;
    padding-bottom: 5mm;
    border-bottom: 0.5mm solid #0f172a;
  }
  .head h1 {
    margin: 0 0 3mm;
    font-size: 22pt;
    font-weight: 600;
    letter-spacing: 4pt;
  }
  .info {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 2mm 8mm;
    font-size: 9.5pt;
    color: #475569;
  }
  .info b { font-weight: 400; color: #94a3b8; margin-right: 1.5mm; }
  .part { margin-top: 5mm; }
  .part h2 {
    margin: 0 0 2mm;
    padding-left: 2.5mm;
    border-left: 1.4mm solid #0f172a;
    font-size: 12pt;
    font-weight: 600;
    letter-spacing: 1pt;
  }
  .part .body {
    font-size: 11pt;
    line-height: 1.95;
    color: #1e293b;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    text-align: justify;
  }
  .foot {
    margin-top: auto;
    padding-top: 4mm;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #94a3b8;
    border-top: 0.2mm solid #e2e8f0;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; width: 210mm; min-height: auto; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
