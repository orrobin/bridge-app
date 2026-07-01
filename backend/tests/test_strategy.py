from app.agents.strategy import HeuristicStrategyProvider

provider = HeuristicStrategyProvider()


def test_disinterest_signal_yields_only_graceful_exit_options():
    conversation = (
        "SPEAKER_1: hey are you free this weekend?\n"
        "SPEAKER_2: honestly I'm not interested, sorry"
    )
    output = provider.generate(conversation, [])

    assert output.disinterest_detected is True
    assert len(output.options) >= 1
    pursuing_phrases = ["one more chance", "give it a try", "just one date", "reconsider"]
    for option in output.options:
        assert not any(phrase in option.message.lower() for phrase in pursuing_phrases)
        assert not option.is_meeting_suggestion


def test_mutual_signals_include_a_meeting_suggestion_option():
    conversation = (
        "SPEAKER_1: I'd would love to hang out sometime\n"
        "SPEAKER_2: same! I'm free this weekend actually"
    )
    output = provider.generate(conversation, [])

    assert output.mutual_signals_detected is True
    assert output.disinterest_detected is False
    assert any(option.is_meeting_suggestion for option in output.options)


def test_neutral_conversation_returns_authentic_options_without_meeting_suggestion():
    conversation = "SPEAKER_1: what kind of music do you like?\nSPEAKER_2: mostly indie rock"
    output = provider.generate(conversation, [])

    assert output.disinterest_detected is False
    assert 2 <= len(output.options) <= 3
    assert not any(option.is_meeting_suggestion for option in output.options)
