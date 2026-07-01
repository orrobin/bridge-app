import pytest
from pydantic import ValidationError

from app.agents.eq import HeuristicEQProvider
from app.schemas.reasoning import EmotionalRead

provider = HeuristicEQProvider()


def test_every_emotional_read_includes_a_counter_read():
    conversation = "SPEAKER_1: haha that's hilarious!\nSPEAKER_2: ok"
    reads = provider.analyze(conversation)

    assert len(reads) >= 1
    for read in reads:
        assert read.counter_read
        assert read.confidence in ("low", "medium", "high")


def test_counter_read_is_enforced_by_schema_not_optional():
    with pytest.raises(ValidationError):
        EmotionalRead(read="seems happy", confidence="low")


def test_neutral_conversation_still_produces_a_hedged_read():
    reads = provider.analyze("SPEAKER_1: sure\nSPEAKER_2: sounds good")
    assert len(reads) >= 1
    assert reads[0].counter_read
