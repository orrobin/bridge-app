import re
from dataclasses import dataclass

# WhatsApp export line, e.g. "6/25/26, 10:14 PM - Alex: hey, how's it going?"
_WHATSAPP_LINE_RE = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?:\s?[APap][Mm])?\s*-\s*([^:]+):\s*(.*)$"
)
# Generic pasted paste, e.g. "Alex: hey, how's it going?"
_GENERIC_LINE_RE = re.compile(r"^([^:\n]{1,80}):\s+(.*)$")


class ChatParseError(ValueError):
    """Raised when the uploaded text can't be parsed into speaker turns."""


@dataclass(frozen=True)
class ParsedTurn:
    speaker: str
    text: str


def parse_chat_export(raw_text: str) -> list[ParsedTurn]:
    if not raw_text or not raw_text.strip():
        raise ChatParseError("Uploaded chat is empty")

    turns: list[ParsedTurn] = []
    current: ParsedTurn | None = None

    for line in raw_text.splitlines():
        if not line.strip():
            continue

        match = _WHATSAPP_LINE_RE.match(line) or _GENERIC_LINE_RE.match(line)
        if match:
            speaker, text = match.group(1).strip(), match.group(2).strip()
            current = ParsedTurn(speaker=speaker, text=text)
            turns.append(current)
        elif current is not None:
            # continuation of a multi-line message
            turns[-1] = ParsedTurn(speaker=current.speaker, text=f"{current.text}\n{line.strip()}")
            current = turns[-1]
        else:
            raise ChatParseError(
                "Could not find a speaker label (e.g. 'Name: message') on line: "
                f"{line[:80]!r}"
            )

    if not turns:
        raise ChatParseError("No message turns could be parsed from the uploaded chat")

    distinct_speakers = {turn.speaker for turn in turns}
    if len(distinct_speakers) < 2:
        raise ChatParseError(
            "Expected at least two distinct speakers in the conversation, found "
            f"{len(distinct_speakers)}"
        )

    return turns
