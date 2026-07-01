from app.agents.analyst import HeuristicAnalystProvider

provider = HeuristicAnalystProvider()


def test_analyst_output_includes_at_least_one_citation():
    context = [("bids-for-connection", "Bids for connection are small moments...")]
    conversation = "SPEAKER_1: hey how's it going?\nSPEAKER_2: good, you?"

    hypotheses = provider.analyze(conversation, context)

    assert len(hypotheses) >= 1
    assert any(h.citations for h in hypotheses)


def test_analyst_never_states_bare_numeric_certainty():
    context = [("bids-for-connection", "some content")]
    conversation = "SPEAKER_1: hey?\nSPEAKER_2: hi"

    hypotheses = provider.analyze(conversation, context)

    for h in hypotheses:
        assert h.confidence in ("low", "medium", "high")
        assert h.counter_evidence
        # never claims a bare percentage/score in the claim text itself
        assert "%" not in h.claim
