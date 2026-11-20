"""教案数据模型：分节文本解析、字段校验与编码识别。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

MAX_TITLE = 40
MAX_META = 20
MAX_HEADING = 12
MAX_BODY = 3000
META_KEYS = ("科目", "班级", "课时", "执教", "日期")
KNOWN_HEADINGS = frozenset(
    (
        "课题",
        "科目",
        "班级",
        "课时",
        "执教",
        "日期",
        "教学目标",
        "教学要求",
        "教学重点",
        "教学难点",
        "教学准备",
        "学情分析",
        "教学过程",
        "教学活动",
        "设计意图",
        "板书设计",
        "作业布置",
        "课后作业",
        "教学反思",
        "教学小结",
        "评价方式",
    )
)


class LessonplanError(ValueError):
    """教案文本或参数不合法。"""


@dataclass(frozen=True)
class LessonPlan:
    """一份教案：标题、元信息与若干小节。"""

    title: str
    subject: str = ""
    grade: str = ""
    periods: str = ""
    sections: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        title = _clean(self.title, "课题")
        if not title:
            raise LessonplanError("课题不能为空")
        if len(title) > MAX_TITLE:
            raise LessonplanError(
                "课题最多 %d 个字符，当前 %d 个" % (MAX_TITLE, len(title))
            )
        subject = _clean(self.subject, "科目")
        grade = _clean(self.grade, "班级")
        periods = _clean(self.periods, "课时")
        for value, label in ((subject, "科目"), (grade, "班级"), (periods, "课时")):
            if len(value) > MAX_META:
                raise LessonplanError("%s最多 %d 个字符" % (label, MAX_META))
        sections: List[Tuple[str, str]] = []
        for heading, body in self.sections:
            name = _clean(heading, "小节标题")
            text = _clean(body, "小节内容")
            if not name:
                raise LessonplanError("小节标题不能为空")
            if len(name) > MAX_HEADING:
                raise LessonplanError(
                    "小节标题最多 %d 个字符：%s" % (MAX_HEADING, name)
                )
            if not text:
                raise LessonplanError("小节「%s」的内容不能为空" % name)
            if len(text) > MAX_BODY:
                raise LessonplanError("小节「%s」的内容过长" % name)
            sections.append((name, text))
        if not sections:
            raise LessonplanError("至少需要一个小节")
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "grade", grade)
        object.__setattr__(self, "periods", periods)
        object.__setattr__(self, "sections", tuple(sections))

    def section(self, heading: str) -> str:
        """按标题取小节内容，不存在时返回空串。"""
        for name, body in self.sections:
            if name == heading:
                return body
        return ""


def _clean(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise LessonplanError("%s必须是文本，当前是 %r" % (label, value))
    return value.strip()


def _decode(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise LessonplanError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise LessonplanError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def _split_header(line: str) -> Tuple[str, str]:
    """把「标题：内容」拆成两段；不是小节标题时返回空标题。"""
    for colon in ("：", ":"):
        index = line.find(colon)
        if index <= 0:
            continue
        heading = line[:index].strip()
        rest = line[index + 1 :].strip()
        if not heading or len(heading) > MAX_HEADING:
            continue
        if any(char in heading for char in "，。；、 "):
            continue
        return heading, rest
    return "", ""


def parse_text(text: str, source: str = "输入内容") -> LessonPlan:
    """解析分节文本：以「小节：」开头，正文直到下一个小节。"""
    if not isinstance(text, str):
        raise LessonplanError("教案内容必须是文本")
    text = text.lstrip("\ufeff")

    title = ""
    meta: Dict[str, str] = {}
    sections: List[Tuple[str, str]] = []
    heading = ""
    buffer: List[str] = []
    heading_lines: Dict[str, int] = {}

    def flush() -> None:
        nonlocal buffer
        if not heading:
            return
        body = "\n".join(buffer).strip()
        if not body:
            raise LessonplanError("小节「%s」没有内容" % heading)
        sections.append((heading, body))
        buffer = []

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        name, rest = _split_header(line.strip())
        is_header = bool(name) and (name in KNOWN_HEADINGS or not rest)
        if is_header:
            flush()
            if name in heading_lines:
                raise LessonplanError(
                    "第 %d 行的「%s」与第 %d 行重复"
                    % (line_no, name, heading_lines[name])
                )
            heading_lines[name] = line_no
            if name == "课题":
                if title:
                    raise LessonplanError("课题重复出现")
                if not rest:
                    raise LessonplanError("第 %d 行课题不能为空" % line_no)
                title = rest
                heading = ""
                continue
            if name in META_KEYS:
                meta[name] = rest
                heading = ""
                continue
            if rest:
                buffer = [rest]
            else:
                buffer = []
            heading = name
            continue
        if not line.strip():
            if heading:
                buffer.append("")
            continue
        if not heading:
            raise LessonplanError(
                "第 %d 行内容不属于任何小节：%s" % (line_no, line.strip())
            )
        buffer.append(line)

    flush()
    if not title:
        raise LessonplanError("缺少「课题：」标题")
    if not sections:
        raise LessonplanError("至少需要一个带正文的小节")

    return LessonPlan(
        title=title,
        subject=meta.get("科目", ""),
        grade=meta.get("班级", ""),
        periods=meta.get("课时", ""),
        sections=tuple(sections),
    )


def load_plan(path: Union[str, Path]) -> LessonPlan:
    """读取教案文本文件。"""
    target = Path(path)
    return parse_text(_decode(target.read_bytes()), source=str(target))


def format_plan(plan: LessonPlan) -> str:
    """把教案写回分节文本，方便保存与修改。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    lines = ["课题：%s" % plan.title]
    if plan.subject:
        lines.append("科目：%s" % plan.subject)
    if plan.grade:
        lines.append("班级：%s" % plan.grade)
    if plan.periods:
        lines.append("课时：%s" % plan.periods)
    for heading, body in plan.sections:
        lines.append("")
        lines.append("%s：" % heading)
        lines.extend(body.splitlines())
    return "\n".join(lines) + "\n"


def section_names(plan: LessonPlan) -> List[str]:
    """教案小节标题列表。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    return [heading for heading, _ in plan.sections]


def meta_items(plan: LessonPlan) -> List[Tuple[str, str]]:
    """非空的元信息，用于渲染标题下方的信息行。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    items: List[Tuple[str, str]] = []
    if plan.subject:
        items.append(("科目", plan.subject))
    if plan.grade:
        items.append(("班级", plan.grade))
    if plan.periods:
        items.append(("课时", plan.periods))
    return items


def total_chars(plan: LessonPlan) -> int:
    """正文总字数，用于页脚统计。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    return sum(len(body) for _, body in plan.sections)


def iter_lines(plan: LessonPlan) -> Sequence[Tuple[str, str]]:
    """扁平化小节内容，便于逐行渲染。"""
    if not isinstance(plan, LessonPlan):
        raise LessonplanError("plan 必须是 LessonPlan 对象")
    return plan.sections
