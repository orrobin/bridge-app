from app.core.chat_parser import ParsedTurn
from app.core.redaction import redact_turns


def test_speaker_names_replaced_with_generic_tokens():
    turns = [
        ParsedTurn(speaker="Alex", text="hey, how's it going?"),
        ParsedTurn(speaker="Jordan", text="good! you?"),
    ]
    redacted = redact_turns(turns)
    assert redacted[0]["speaker"] == "SPEAKER_1"
    assert redacted[1]["speaker"] == "SPEAKER_2"
    assert "Alex" not in str(redacted)
    assert "Jordan" not in str(redacted)


def test_self_mention_of_name_in_text_is_redacted():
    turns = [
        ParsedTurn(speaker="Alex", text="it's Alex here, nice to meet you Jordan"),
        ParsedTurn(speaker="Jordan", text="hi!"),
    ]
    redacted = redact_turns(turns)
    assert "Alex" not in redacted[0]["text"]
    assert "Jordan" not in redacted[0]["text"]
    assert "SPEAKER_1" in redacted[0]["text"]
    assert "SPEAKER_2" in redacted[0]["text"]


def test_email_is_redacted():
    turns = [
        ParsedTurn(speaker="Alex", text="email me at alex@example.com"),
        ParsedTurn(speaker="Jordan", text="ok"),
    ]
    redacted = redact_turns(turns)
    assert "alex@example.com" not in redacted[0]["text"]
    assert "[EMAIL]" in redacted[0]["text"]


def test_phone_number_is_redacted():
    turns = [
        ParsedTurn(speaker="Alex", text="call me at 555-123-4567"),
        ParsedTurn(speaker="Jordan", text="ok"),
    ]
    redacted = redact_turns(turns)
    assert "555-123-4567" not in redacted[0]["text"]
    assert "[PHONE]" in redacted[0]["text"]


def test_handle_and_url_are_redacted():
    turns = [
        ParsedTurn(speaker="Alex", text="follow me @alex_123 or check https://example.com/alex"),
        ParsedTurn(speaker="Jordan", text="ok"),
    ]
    redacted = redact_turns(turns)
    assert "@alex_123" not in redacted[0]["text"]
    assert "[HANDLE]" in redacted[0]["text"]
    assert "[URL]" in redacted[0]["text"]
    assert "https://example.com/alex" not in redacted[0]["text"]
