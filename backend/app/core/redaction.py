import re

from app.core.chat_parser import ParsedTurn

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL_RE = re.compile(r"https?://\S+")
_HANDLE_RE = re.compile(r"(?<!\w)@\w+")
# Loose match for phone-number-shaped runs of digits/separators (7+ digits).
_PHONE_RE = re.compile(r"(?<!\w)(\+?\d[\d\-.\s()]{5,}\d)(?!\w)")

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_EMAIL_RE, "[EMAIL]"),
    (_URL_RE, "[URL]"),
    (_HANDLE_RE, "[HANDLE]"),
    (_PHONE_RE, "[PHONE]"),
]


def _redact_pii(text: str) -> str:
    for pattern, placeholder in _PII_PATTERNS:
        text = pattern.sub(placeholder, text)
    return text


def redact_turns(turns: list[ParsedTurn]) -> list[dict[str, str]]:
    """Redact PII and speaker names before anything is persisted or sent to an LLM.

    Speaker labels are replaced with generic SPEAKER_n tokens (in order of first
    appearance), and any self-mentions of those names within message text are
    also replaced, since real names must never reach storage or a model call.
    """
    speaker_placeholders: dict[str, str] = {}
    for turn in turns:
        if turn.speaker not in speaker_placeholders:
            speaker_placeholders[turn.speaker] = f"SPEAKER_{len(speaker_placeholders) + 1}"

    redacted: list[dict[str, str]] = []
    for turn in turns:
        text = turn.text
        for name, placeholder in speaker_placeholders.items():
            if name:
                text = re.sub(re.escape(name), placeholder, text, flags=re.IGNORECASE)
        text = _redact_pii(text)
        redacted.append({"speaker": speaker_placeholders[turn.speaker], "text": text})

    return redacted
