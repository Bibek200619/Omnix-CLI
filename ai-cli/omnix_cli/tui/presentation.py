"""Terminal-native branding, semantic themes, readable output and artifact diffs."""

from __future__ import annotations

import difflib
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.artifacts import Artifact

PIXEL_MARK = (
    "         BBAAAAAAB          ",
    "     BAWWWWWWWWWWWWWAAB     ",
    "   BWWWWWWWWWWWWWWWWWWWAB   ",
    "  AWWWWWWWAAB   BAAAAAAAAB  ",
    " AWWWWWWWA        BAAAAAAAB ",
    " AWWWWWWWB         BAAAAAAB ",
    " BWWWWWWWA         AAAAAAAB ",
    "  AWWWWWAABB    BBAAAAAAAB  ",
    "   BAAAAAAAAAAAAAAAAAAAAB   ",
    "      BAAAAAAAAAAAAAAB      ",
    "          BBBBBBBB          ",
)
THEMES = ("slate", "light", "terminal", "mono")
# Strip complete ANSI/OSC sequences, then remaining terminal control characters.
ESCAPES = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]")
CONTROLS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def clean(text: str) -> str:
    return CONTROLS.sub("", ESCAPES.sub("", text.replace("\r\n", "\n")))


def ascii_mode() -> bool:
    return os.environ.get("OMNIX_ASCII", "").lower() in {"1", "true", "yes"}


def logo() -> StyleAndTextTuples:
    glyph = "#" if ascii_mode() else "█"
    tones = {"W": "class:logo.light", "A": "class:accent", "B": "class:logo.shadow"}
    return _logo_rows(glyph, tones)


def _logo_rows(glyph: str, tones: dict[str, str]) -> StyleAndTextTuples:
    result: StyleAndTextTuples = []
    for index, row in enumerate(PIXEL_MARK):
        result.extend((tones.get(c, ""), glyph if c != " " else " ") for c in row)
        if index < len(PIXEL_MARK) - 1:
            result.append(("", "\n"))
    return result


def theme_style(theme: str, no_color: bool = False) -> Style:
    if no_color or theme == "mono":
        return Style.from_dict({"selected": "reverse", "heading": "bold"})
    if theme == "terminal":
        return Style.from_dict(
            {
                "selected": "reverse",
                "heading": "bold",
                "add": "ansigreen",
                "delete": "ansired",
                "error": "ansired",
                "warning": "ansiyellow",
            }
        )
    light = theme == "light"
    return Style.from_dict(
        {
            "": "bg:#eef2f7 #17273d" if light else "bg:#182333 #eaf1fc",
            "input": "bg:#dce5ef #17273d" if light else "bg:#223246 #eaf1fc",
            "context": "bg:#dce5ef #17273d" if light else "bg:#223246 #eaf1fc",
            "muted": "#435975" if light else "#b2c2d8",
            "accent": "#2559ad" if light else "#a6c8ff",
            "heading": "bold #2559ad" if light else "bold #a6c8ff",
            "selected": "noreverse bg:#2559ad #ffffff" if light else "noreverse bg:#304c75 #eaf1fc",
            "add": "bg:#d4eadc #185b31" if light else "bg:#203c36 #b4e5c2",
            "delete": "bg:#f4dce1 #842d3e" if light else "bg:#422d3b #f0b2ba",
            "error": "#842d3e" if light else "#f0adb6",
            "warning": "#755019" if light else "#eacb93",
            "logo.light": "#2559ad" if light else "#d9e9ff",
            "logo.shadow": "#435975" if light else "#6a91cf",
        }
    )


class TranscriptLexer(Lexer):
    def lex_document(self, document: Document) -> Callable[[int], StyleAndTextTuples]:
        def line(number: int) -> StyleAndTextTuples:
            text = document.lines[number]
            style = ""
            if text.startswith("+ "):
                style = "class:add"
            elif text.startswith("- "):
                style = "class:delete"
            elif text.startswith(("Failed", "Interrupted")):
                style = "class:error"
            elif text.startswith(("You", "Master", "Running /", "Saved artifact", "@@")):
                style = "class:heading"
            return [(style, text)]

        return line


@dataclass
class Patch:
    path: str
    before: str
    after: str
    expanded: bool = True

    def lines(self) -> list[str]:
        raw = list(difflib.unified_diff(self.before.splitlines(), self.after.splitlines(), n=3))
        added = sum(x.startswith("+") and not x.startswith("+++") for x in raw)
        removed = sum(x.startswith("-") and not x.startswith("---") for x in raw)
        summary = f"Saved artifact {clean(self.path)} (+{added} -{removed})"
        if not self.expanded:
            return [summary + " [collapsed; /changes to expand]"]
        result = [summary, "  old   new  content"]
        old = new = 0
        for row in raw[2:202]:
            if row.startswith("@@"):
                match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", row)
                if match:
                    old, new = map(int, match.groups())
                result.append(row)
            elif row.startswith("+"):
                result.append(f"+      {new:>4}  {clean(row[1:])}")
                new += 1
            elif row.startswith("-"):
                result.append(f"- {old:>4}        {clean(row[1:])}")
                old += 1
            else:
                result.append(f"  {old:>4} {new:>4}  {clean(row[1:])}")
                old += 1
                new += 1
        if len(raw) > 202:
            result.append(
                "[Patch display limited to 200 lines; inspect the saved artifact for more.]"
            )
        result.append("Generated content saved locally; application source was not applied.")
        return result


@dataclass
class Entry:
    heading: str
    text: str = ""
    patches: list[Patch] = field(default_factory=list)

    def render(self) -> str:
        blocks = [clean(self.heading), clean(self.text)]
        blocks.extend("\n".join(p.lines()) for p in self.patches)
        return "\n".join(x for x in blocks if x)


def artifact_snapshot(workspace: Path) -> dict[str, str]:
    """Read a bounded set of artifact bodies, never arbitrary application files."""
    result: dict[str, str] = {}
    root = workspace / ".project" / "artifacts"
    for path in sorted(root.glob("*.json"))[:256]:
        try:
            if path.is_symlink() or path.stat().st_size > 1_048_576:
                continue
            artifact = Artifact.model_validate_json(path.read_text(encoding="utf-8"))
            result[f".project/artifacts/{path.name}"] = artifact.content
        except (OSError, ValueError):
            continue
    return result


def artifact_changes(before: dict[str, str], after: dict[str, str]) -> list[Patch]:
    return [
        Patch(path, before.get(path, ""), body)
        for path, body in after.items()
        if before.get(path) != body
    ]


def project_context(workspace: Path) -> tuple[str, str, str]:
    """Read configuration without contacting providers or creating account state."""
    state = StateManager(workspace)
    if not state.project_dir.exists():
        return workspace.name, "Local / unconfigured", "Not initialized. Start with /init."
    try:
        blueprint = state.load_blueprint()
        memory = state.load_memory()
        models = state.load_models()
        model = models.master
        assignment = f"{model.provider or 'unset'}:{model.model or 'unset'}" if model else "Local"
        details = (
            f"Project\n{blueprint.project_name or workspace.name}\n\n"
            f"Agent\nMaster\n\nModel\n{assignment}\n\n"
            f"Context\n{len(memory.goals)} goals\n{len(memory.decisions)} decisions\n"
            f"{len(memory.conversations)} messages\n\n"
            "Storage\n.project/\n\n"
            "Specialists\nExplicit invocation\n\n"
            "Providers\nConfiguration is not a live connection check.\n\n"
            "Account\nUse /status to check."
        )
        return clean(blueprint.project_name or workspace.name), clean(assignment), clean(details)
    except (OmnixError, OSError, ValueError) as exc:
        return workspace.name, "Invalid state", clean(str(exc))
