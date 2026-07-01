import pytest

from app.core.chat_parser import ChatParseError, parse_chat_export


def test_parses_generic_speaker_lines():
    raw = "Alex: hey, how's it going?\nJordan: good! you?"
    turns = parse_chat_export(raw)
    assert [t.speaker for t in turns] == ["Alex", "Jordan"]
    assert turns[0].text == "hey, how's it going?"


def test_parses_whatsapp_export_format():
    raw = (
        "6/25/26, 10:14 PM - Alex: hey, how's it going?\n"
        "6/25/26, 10:15 PM - Jordan: good! you?"
    )
    turns = parse_chat_export(raw)
    assert [t.speaker for t in turns] == ["Alex", "Jordan"]
    assert turns[1].text == "good! you?"


def test_multiline_message_is_appended_to_previous_turn():
    raw = "Alex: hey\nstill there?\nJordan: yeah, sorry"
    turns = parse_chat_export(raw)
    assert turns[0].text == "hey\nstill there?"


def test_empty_input_raises_chat_parse_error():
    with pytest.raises(ChatParseError):
        parse_chat_export("   ")


def test_unparseable_line_raises_chat_parse_error():
    with pytest.raises(ChatParseError):
        parse_chat_export("this has no speaker label at all")


def test_single_speaker_raises_chat_parse_error():
    with pytest.raises(ChatParseError):
        parse_chat_export("Alex: hey\nAlex: are you there?")
