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

    def __str__(self) -> str:
        prefix = {
            LogType.Warning: "\u2757",
            LogType.Error: "\u274C",
        }[self.type]
        return f"{prefix} {self.text}"

    def to_text(self) -> str:
        return f"{self.type.name}: {self.text}"


class ListLogger(Outputter):
    def __init__(self, reference: list[LogEntry], type: LogType):
        self.reference = reference
        self.type = type

    def handle(self, description, content):
        entry = LogEntry(self.type, str(description))
        self.reference.append(entry)
