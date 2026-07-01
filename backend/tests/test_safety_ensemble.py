from app.agents.safety import EnsembleSafetyClassifier, SafetyDecision


class _StubClassifier:
    """Fake classifier returning a fixed decision -- no API calls, pure logic test."""

    def __init__(self, decision: str, reason: str = "stub reason") -> None:
        self._decision = SafetyDecision(decision, reason)

    def classify_pre_screen(self, conversation_text: str) -> SafetyDecision:
        return self._decision

    def classify_post_gate(self, draft_reply: str) -> SafetyDecision:
        return self._decision


def test_ensemble_uses_rule_based_block_even_if_llm_says_allow():
    ensemble = EnsembleSafetyClassifier(
        rule_based=_StubClassifier("block", "rule matched"),
        llm=_StubClassifier("allow", "llm saw nothing"),
    )
    result = ensemble.classify_pre_screen("anything")
    assert result.decision == "block"
    assert "rule-based" in result.reason


def test_ensemble_uses_llm_escalate_even_if_rules_say_allow():
    ensemble = EnsembleSafetyClassifier(
        rule_based=_StubClassifier("allow", "no pattern matched"),
        llm=_StubClassifier("escalate", "llm caught a crisis signal"),
    )
    result = ensemble.classify_post_gate("anything")
    assert result.decision == "escalate"
    assert "llm" in result.reason


def test_ensemble_allows_only_when_both_allow():
    ensemble = EnsembleSafetyClassifier(
        rule_based=_StubClassifier("allow"),
        llm=_StubClassifier("allow"),
    )
    result = ensemble.classify_pre_screen("hey how's it going")
    assert result.decision == "allow"


def test_ensemble_escalate_beats_block_regardless_of_source():
    ensemble = EnsembleSafetyClassifier(
        rule_based=_StubClassifier("block"),
        llm=_StubClassifier("escalate"),
    )
    result = ensemble.classify_pre_screen("anything")
    assert result.decision == "escalate"
