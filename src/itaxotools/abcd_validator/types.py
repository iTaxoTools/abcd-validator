from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from abcd_converter_gfbio_org.handlers import Outputter


class LogType(Enum):
    Warning = auto()
    Error = auto()


@dataclass
class LogEntry:
    type: LogType
    text: str
    content: dict[str, str]

    def __str__(self) -> str:
        prefix = {
            LogType.Warning: "\u2757",
            LogType.Error: "\u274C",
        }[self.type]
        return f"{prefix} {self.file_content_to_text()}{self.text} {self.message_content_to_text()} {repr(self.content)}"

    def to_text(self) -> str:
        return f"{self.type.name}: {self.file_content_to_text()}{self.text} {self.message_content_to_text()} {repr(self.content)}"

    def file_content_to_text(self) -> str:
        file = self.content.get("file", "")
        if not file:
            return ""
        if file == "result":
            return "In scheme validation: "
        return f"In {file.lower()} table: "

    def message_content_to_text(self) -> str:
        message = self.content.get("message", "")
        if not message:
            return ""
        message = message.replace("\n", "")
        return f"<{message}>"


class ListLogger(Outputter):
    def __init__(self, reference: list[LogEntry], type: LogType):
        self.reference = reference
        self.type = type

    def handle(self, description, content):
        entry = LogEntry(self.type, str(description), content)
        self.reference.append(entry)
