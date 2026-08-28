from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


UTF16_LE_BOM = b"\xff\xfe"
TOPIC_FIELDS = (
    "Title",
    "Level",
    "Url",
    "Icon",
    "Status",
    "Keywords",
    "ContextNumber",
    "ApplyTemp",
    "Expanded",
    "Kind",
)
TOPIC_RE = re.compile(r"^TitleList\.([^.]+)\.(\d+)=(.*)$")
NATURAL_PART_RE = re.compile(r"(\d+)")
SEPARATOR_RE = re.compile(r"^[\s\-—–─━_=*·•]+$")


class WcpError(ValueError):
    pass


@dataclass
class Topic:
    original_index: int
    values: dict[str, str]
    children: list["Topic"] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.values.get("Title", "")

    @property
    def level(self) -> int:
        try:
            return int(self.values["Level"])
        except (KeyError, ValueError) as exc:
            raise WcpError(
                f"条目 {self.original_index} 的 Level 不是整数"
            ) from exc


@dataclass
class WcpProject:
    prefix_lines: list[str]
    topics: list[Topic]
    extra_field_order: list[str]


@dataclass
class ContextStats:
    preserved: int = 0
    assigned: int = 0
    cleared_for_container: int = 0
    repaired_duplicates: int = 0


def read_wcp(path: Path) -> WcpProject:
    data = path.read_bytes()
    if not data.startswith(UTF16_LE_BOM):
        raise WcpError("文件不是带 BOM 的 UTF-16LE WCP")

    try:
        text = data[len(UTF16_LE_BOM) :].decode("utf-16-le")
    except UnicodeDecodeError as exc:
        raise WcpError("WCP 的 UTF-16LE 内容无法解码") from exc

    lines = text.splitlines()
    try:
        topics_header = lines.index("[TOPICS]")
    except ValueError as exc:
        raise WcpError("找不到 [TOPICS] 段") from exc

    if topics_header + 1 >= len(lines) or not lines[topics_header + 1].startswith(
        "TitleList="
    ):
        raise WcpError("[TOPICS] 后缺少 TitleList=数量")

    declared_text = lines[topics_header + 1].partition("=")[2]
    try:
        declared_count = int(declared_text)
    except ValueError as exc:
        raise WcpError(f"TitleList 数量不是整数: {declared_text!r}") from exc

    values_by_index: dict[int, dict[str, str]] = {}
    field_order: list[str] = []
    for line_number, line in enumerate(lines[topics_header + 2 :], topics_header + 3):
        if not line:
            continue
        match = TOPIC_RE.fullmatch(line)
        if not match:
            raise WcpError(f"第 {line_number} 行不是合法的 TitleList 字段: {line!r}")
        field_name, index_text, value = match.groups()
        index = int(index_text)
        record = values_by_index.setdefault(index, {})
        if field_name in record:
            raise WcpError(f"条目 {index} 的 {field_name} 字段重复")
        record[field_name] = value
        if field_name not in field_order:
            field_order.append(field_name)

    if len(values_by_index) != declared_count:
        raise WcpError(
            f"TitleList 声明 {declared_count} 条，实际解析到 {len(values_by_index)} 条"
        )

    topics: list[Topic] = []
    for index in sorted(values_by_index):
        values = values_by_index[index]
        missing = [name for name in TOPIC_FIELDS if name not in values]
        if missing:
            raise WcpError(f"条目 {index} 缺少字段: {', '.join(missing)}")
        topics.append(Topic(index, values))

    validate_levels(topics)
    extra_fields = [name for name in field_order if name not in TOPIC_FIELDS]
    prefix_lines = lines[: topics_header + 1]
    return WcpProject(prefix_lines, topics, extra_fields)


def validate_levels(topics: list[Topic]) -> None:
    previous_level = 0
    for position, topic in enumerate(topics):
        level = topic.level
        if level < 0:
            raise WcpError(f"条目 {topic.original_index} 的 Level 不能为负数")
        if position == 0 and level != 0:
            raise WcpError("第一个目录条目的 Level 必须是 0")
        if position and level > previous_level + 1:
            raise WcpError(
                f"条目 {topic.original_index} 从 Level {previous_level} 跳到 {level}"
            )
        previous_level = level


def build_tree(topics: list[Topic]) -> list[Topic]:
    roots: list[Topic] = []
    stack: list[Topic] = []
    for topic in topics:
        topic.children = []
        level = topic.level
        if level == 0:
            roots.append(topic)
        else:
            if len(stack) < level:
                raise WcpError(f"条目 {topic.original_index} 找不到 Level {level - 1} 父节点")
            stack[level - 1].children.append(topic)
        if len(stack) <= level:
            stack.append(topic)
        else:
            stack[level] = topic
            del stack[level + 1 :]
    return roots


def natural_key(text: str) -> tuple[tuple[int, object], ...]:
    normalized = unicodedata.normalize("NFC", text).casefold()
    parts = NATURAL_PART_RE.split(normalized)
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in parts
        if part
    )


def sort_children(nodes: list[Topic], recursive: bool) -> None:
    sorted_nodes: list[Topic] = []
    sortable_run: list[Topic] = []

    def flush_run() -> None:
        sortable_run.sort(
            key=lambda topic: (natural_key(topic.title), topic.original_index)
        )
        sorted_nodes.extend(sortable_run)
        sortable_run.clear()

    for topic in nodes:
        if SEPARATOR_RE.fullmatch(topic.title):
            flush_run()
            sorted_nodes.append(topic)
        else:
            sortable_run.append(topic)
    flush_run()
    nodes[:] = sorted_nodes
    if recursive:
        for topic in nodes:
            sort_children(topic.children, recursive=True)


def apply_requested_sort(
    roots: list[Topic], parent_titles: list[str], sort_all_siblings: bool
) -> int:
    matched = 0
    matched_titles: set[str] = set()

    def visit(topic: Topic) -> None:
        nonlocal matched
        if topic.title in parent_titles:
            sort_children(topic.children, recursive=False)
            matched += 1
            matched_titles.add(topic.title)
        if sort_all_siblings:
            sort_children(topic.children, recursive=False)
        for child in topic.children:
            visit(child)

    if sort_all_siblings:
        # The root order is editorial (core rules, expansions, settings, etc.).
        # Keep it intact and sort only children below each root.
        for root in roots:
            sort_children(root.children, recursive=True)
    else:
        for root in roots:
            visit(root)

    missing = sorted(set(parent_titles) - matched_titles)
    if missing:
        raise WcpError(
            "找不到以下 --sort-parent 目录标题: " + ", ".join(missing)
        )
    return matched


def flatten_tree(roots: list[Topic]) -> list[Topic]:
    result: list[Topic] = []

    def visit(topic: Topic, level: int) -> None:
        topic.values["Level"] = str(level)
        result.append(topic)
        for child in topic.children:
            visit(child, level + 1)

    for root in roots:
        visit(root, 0)
    return result


def repair_context_numbers(topics: list[Topic], start: int | None) -> ContextStats:
    stats = ContextStats()
    numeric_values = [
        int(topic.values["ContextNumber"])
        for topic in topics
        if topic.values["ContextNumber"].isdigit()
    ]
    next_context = start if start is not None else max(numeric_values, default=999) + 1
    if next_context < 1:
        raise WcpError("ContextNumber 起始值必须大于 0")

    used: set[int] = set()
    for topic in topics:
        url = topic.values["Url"].strip()
        status = topic.values["Status"]
        raw_context = topic.values["ContextNumber"].strip()
        is_container = not url or status == "2"

        if is_container:
            if raw_context:
                topic.values["ContextNumber"] = ""
                stats.cleared_for_container += 1
            continue

        old_context = int(raw_context) if raw_context.isdigit() else None
        if old_context is not None and old_context > 0 and old_context not in used:
            used.add(old_context)
            stats.preserved += 1
            continue

        if old_context is not None and old_context in used:
            stats.repaired_duplicates += 1
        while next_context in used:
            next_context += 1
        topic.values["ContextNumber"] = str(next_context)
        used.add(next_context)
        next_context += 1
        stats.assigned += 1
    return stats


def validate_urls(project_path: Path, topics: list[Topic]) -> list[str]:
    warnings: list[str] = []
    project_root = project_path.parent.resolve()
    for topic in topics:
        url = topic.values["Url"].strip()
        if not url:
            continue
        if re.match(r"^[A-Za-z]:[\\/]", url) or url.startswith(("\\\\", "//")):
            raise WcpError(f"条目 {topic.original_index} 使用绝对 URL: {url}")
        clean_url = re.split(r"[?#]", url, maxsplit=1)[0]
        candidate = (project_root / Path(clean_url.replace("\\", os.sep))).resolve()
        try:
            candidate.relative_to(project_root)
        except ValueError as exc:
            raise WcpError(f"条目 {topic.original_index} 的 URL 越出工程目录: {url}") from exc
        if not candidate.is_file():
            warnings.append(
                f"条目 {topic.original_index} ({topic.title}) 的 URL 不是现存文件: {url}"
            )
    return warnings


def serialize(project: WcpProject, topics: list[Topic]) -> bytes:
    lines = list(project.prefix_lines)
    lines.append(f"TitleList={len(topics)}")
    field_order = list(TOPIC_FIELDS) + project.extra_field_order
    for index, topic in enumerate(topics):
        for field_name in field_order:
            if field_name in topic.values:
                lines.append(f"TitleList.{field_name}.{index}={topic.values[field_name]}")
    text = "\r\n".join(lines) + "\r\n"
    return UTF16_LE_BOM + text.encode("utf-16-le")


def backup_path_for(path: Path) -> Path:
    candidate = path.with_suffix(path.suffix + ".bak")
    counter = 1
    while candidate.exists():
        candidate = path.with_suffix(path.suffix + f".bak.{counter}")
        counter += 1
    return candidate


def atomic_write(path: Path, data: bytes) -> Path:
    backup = backup_path_for(path)
    shutil.copy2(path, backup)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return backup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "整理 WinCHM WCP：连续重建 TitleList 索引、修复 ContextNumber，"
            "并可选择对同级目录进行自然排序。"
        ),
        epilog=(
            "示例：WCP自动整理.py ../不全书.wcp --check | "
            "WCP自动整理.py ../不全书.wcp | "
            "WCP自动整理.py ../不全书.wcp --sort-parent 本书速查"
        ),
    )
    parser.add_argument(
        "wcp", nargs="?", type=Path, help="要整理的 .wcp 文件；省略时弹出选择框"
    )
    parser.add_argument(
        "--check", action="store_true", help="只检查并显示将发生的变化，不写文件"
    )
    parser.add_argument(
        "--sort-parent",
        action="append",
        default=[],
        metavar="标题",
        help="按标题自然排序该目录的直接子项；可重复指定",
    )
    parser.add_argument(
        "--sort-all-siblings",
        action="store_true",
        help="递归排序所有同级子项，但保留顶层来源书和分隔栏顺序",
    )
    parser.add_argument(
        "--context-start",
        type=int,
        help="新 ContextNumber 的起始值；默认从现有最大值加 1 开始",
    )
    parser.add_argument(
        "--skip-url-check", action="store_true", help="不检查目录 URL 是否对应文件"
    )
    return parser.parse_args()


def choose_wcp() -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise WcpError("当前 Python 没有 tkinter，请在命令行提供 WCP 路径") from exc

    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askopenfilename(
            title="选择要自动整理的 WCP 文件",
            initialdir=Path(__file__).resolve().parent.parent,
            filetypes=(("WinCHM 工程", "*.wcp"), ("所有文件", "*.*")),
        )
    finally:
        root.destroy()
    return Path(selected) if selected else None


def main() -> int:
    args = parse_args()
    try:
        selected_path = args.wcp or choose_wcp()
    except WcpError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    if selected_path is None:
        print("已取消")
        return 0
    path = selected_path.resolve()
    if path.suffix.lower() != ".wcp" or not path.is_file():
        print(f"错误：不是现存的 .wcp 文件：{path}", file=sys.stderr)
        return 2

    try:
        project = read_wcp(path)
        roots = build_tree(project.topics)
        matched = apply_requested_sort(
            roots, args.sort_parent, args.sort_all_siblings
        )
        topics = flatten_tree(roots)
        context_stats = repair_context_numbers(topics, args.context_start)
        warnings = [] if args.skip_url_check else validate_urls(path, topics)
        output = serialize(project, topics)
    except WcpError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"条目数：{len(topics)}")
    print(f"保留 ContextNumber：{context_stats.preserved}")
    print(f"新分配 ContextNumber：{context_stats.assigned}")
    print(f"修复重复 ContextNumber：{context_stats.repaired_duplicates}")
    print(f"清空目录节点 ContextNumber：{context_stats.cleared_for_container}")
    if args.sort_parent:
        print(f"已匹配并排序目录：{matched}")
    if args.sort_all_siblings:
        print("已递归自然排序所有同级子项（顶层顺序保持不变）")
    for warning in warnings:
        print(f"警告：{warning}")

    changed = output != path.read_bytes()
    if args.check:
        print("检查结果：文件需要整理" if changed else "检查结果：文件已经规范")
        return 1 if changed or warnings else 0

    if not changed:
        print("文件已经规范，无需写入")
        return 0
    backup = atomic_write(path, output)
    print(f"已写入：{path}")
    print(f"备份：{backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
