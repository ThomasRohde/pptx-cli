from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass(frozen=True)
class ParsedRun:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass(frozen=True)
class ParsedParagraph:
    runs: tuple[ParsedRun, ...]
    level: int | None
    kind: Literal["body", "heading", "bullet", "ordered"] = "body"
    heading_level: int | None = None

    @property
    def text(self) -> str:
        return "".join(run.text for run in self.runs)


@dataclass
class _ListContext:
    ordered: bool
    next_index: int


@dataclass
class _ListItemContext:
    ordered_prefix: str | None
    bullet_level: int | None
    paragraph_count: int = 0


@dataclass
class _InlineStyle:
    bold: bool = False
    italic: bool = False


_MARKDOWN = MarkdownIt("commonmark")
_EMPTY_PARAGRAPH = ParsedParagraph(runs=(ParsedRun(text=""),), level=None)


def looks_like_markdown(text: str) -> bool:
    if "\n" not in text and "\r" not in text:
        return False

    for raw_line in text.splitlines():
        stripped = raw_line.lstrip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ", "+ ", "#", "> ")):
            return True
        if _starts_with_ordered_list_marker(stripped):
            return True
    return False


def parse_plain_text_paragraphs(text: str) -> list[ParsedParagraph]:
    lines = text.splitlines() or [""]
    return [ParsedParagraph(runs=(ParsedRun(text=line),), level=None) for line in lines]


def parse_markdown_paragraphs(markdown: str) -> list[ParsedParagraph]:
    paragraphs: list[ParsedParagraph] = []
    list_stack: list[_ListContext] = []
    current_item: _ListItemContext | None = None
    tokens = _MARKDOWN.parse(markdown)

    for index, token in enumerate(tokens):
        if token.type == "bullet_list_open":
            list_stack.append(_ListContext(ordered=False, next_index=1))
            continue

        if token.type == "ordered_list_open":
            start = _ordered_list_start(token.attrGet("start") if token.attrs else None)
            list_stack.append(_ListContext(ordered=True, next_index=start))
            continue

        if token.type in {"bullet_list_close", "ordered_list_close"}:
            list_stack.pop()
            continue

        if token.type == "list_item_open":
            ordered_prefix: str | None = None
            bullet_level: int | None = None
            if list_stack:
                current_list = list_stack[-1]
                bullet_level = min(len(list_stack) - 1, 4)
                if current_list.ordered:
                    ordered_prefix = f"{current_list.next_index}. "
                    current_list.next_index += 1
            current_item = _ListItemContext(
                ordered_prefix=ordered_prefix,
                bullet_level=bullet_level,
            )
            continue

        if token.type == "list_item_close":
            current_item = None
            continue

        if token.type != "inline":
            continue

        previous_type = tokens[index - 1].type if index > 0 else None
        if previous_type not in {"paragraph_open", "heading_open"}:
            continue

        prefix = None
        level = None
        kind: Literal["body", "heading", "bullet", "ordered"] = "body"
        heading_level: int | None = None
        if previous_type == "heading_open":
            kind = "heading"
            heading_level = _heading_level(tokens[index - 1].tag)
        if current_item is not None:
            level = current_item.bullet_level
            if current_item.paragraph_count == 0:
                prefix = current_item.ordered_prefix
            if current_item.ordered_prefix is not None:
                kind = "ordered"
            elif current_item.bullet_level is not None:
                kind = "bullet"
            current_item.paragraph_count += 1

        runs = tuple(_parse_inline_runs(token.children or [], prefix=prefix))
        paragraphs.append(
            ParsedParagraph(
                runs=runs or _EMPTY_PARAGRAPH.runs,
                level=level,
                kind=kind,
                heading_level=heading_level,
            )
        )

    return paragraphs or [_EMPTY_PARAGRAPH]


def _parse_inline_runs(tokens: list[Token], *, prefix: str | None) -> list[ParsedRun]:
    runs: list[ParsedRun] = []
    style = _InlineStyle()

    if prefix:
        _append_run(runs, ParsedRun(text=prefix))

    for token in tokens:
        token_type = token.type
        if token_type == "text":
            _append_styled_text(runs, token.content, style)
            continue
        if token_type in {"softbreak", "hardbreak"}:
            _append_styled_text(runs, "\n", style)
            continue
        if token_type == "code_inline":
            _append_run(
                runs,
                ParsedRun(
                    text=token.content,
                    bold=style.bold,
                    italic=style.italic,
                    code=True,
                ),
            )
            continue
        if token_type == "strong_open":
            style.bold = True
            continue
        if token_type == "strong_close":
            style.bold = False
            continue
        if token_type == "em_open":
            style.italic = True
            continue
        if token_type == "em_close":
            style.italic = False
            continue
        if token_type == "image":
            _append_styled_text(runs, token.content, style)

    return runs


def _append_styled_text(runs: list[ParsedRun], text: str, style: _InlineStyle) -> None:
    if not text:
        return
    _append_run(runs, ParsedRun(text=text, bold=style.bold, italic=style.italic))


def _append_run(runs: list[ParsedRun], run: ParsedRun) -> None:
    if not run.text:
        return

    if (
        runs
        and runs[-1].bold == run.bold
        and runs[-1].italic == run.italic
        and runs[-1].code == run.code
    ):
        previous = runs[-1]
        runs[-1] = ParsedRun(
            text=previous.text + run.text,
            bold=run.bold,
            italic=run.italic,
            code=run.code,
        )
        return

    runs.append(run)


def _ordered_list_start(raw_start: str | int | float | None) -> int:
    if raw_start is None:
        return 1
    try:
        return int(raw_start)
    except ValueError:
        return 1


def _heading_level(tag: str) -> int | None:
    if len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
        return int(tag[1])
    return None


def _starts_with_ordered_list_marker(text: str) -> bool:
    marker = []
    for character in text:
        if character.isdigit():
            marker.append(character)
            continue
        if character in {".", ")"} and marker:
            remainder = text[len(marker) + 1 :]
            return remainder.startswith(" ")
        return False
    return False
