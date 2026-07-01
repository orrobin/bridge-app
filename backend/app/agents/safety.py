import re
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.llm_client import LLMClient


@dataclass(frozen=True)
class SafetyDecision:
    decision: str  # "allow" | "block" | "escalate"
    reason: str


class SafetyClassifier(Protocol):
    def classify_pre_screen(self, conversation_text: str) -> SafetyDecision: ...
    def classify_post_gate(self, draft_reply: str) -> SafetyDecision: ...


# Escalate (not just block) -- routes to safety resources rather than a silent stop.
_SELF_HARM_PATTERNS = [
    r"\bkill(ing)? myself\b",
    r"\bwant(ed)? to die\b",
    r"\bend(ing)? it all\b",
    r"\bhurt(ing)? myself\b",
    r"\bsuicidal?\b",
    r"\bnot worth living\b",
]

_MINOR_PATTERNS = [
    r"\bi'?m\s+1[0-7]\b",
    r"\b1[0-7]\s*(years?\s*old|y/?o)\b",
    r"\bin (high school|middle school|8th grade|9th grade|10th grade)\b",
    r"\bmy (mom|dad|parents) (said|says|won'?t let me)\b",
]

_COERCION_PATTERNS = [
    r"\bor else\b",
    r"\byou have to (reply|answer|talk to me)\b",
    r"\bi'?ll find (you|where you live)\b",
    r"\bwon'?t stop (messaging|texting|calling)\b",
    r"\byou owe me\b",
    r"\bmake you\b.*\b(talk|reply|see me)\b",
]

# Post-gate: manipulation / pushing past disinterest in an outgoing draft reply.
_MANIPULATION_PATTERNS = [
    r"\byou'?re (pretty|cute|attractive) for\b",  # negging
    r"\bsoulmates?\b",
    r"\bmeant to be together\b",
    r"\bi know you said no\b",
    r"\bjust give me one more (chance|try)\b",
    r"\bone more (chance|try)\b.*\bplease\b",
    r"\bwon'?t wait forever\b",
    r"\bothers? (want|are interested in) me\b",
    r"\blast chance\b",
    r"\bafter everything i'?ve done\b",
]


class RuleBasedSafetyClassifier:
    """Deterministic keyword/pattern classifier.

    This is a legitimate first-pass technique for hard safety triggers (self-harm,
    minors, coercion, manipulation language) on its own -- not merely a fallback.
    Measured against ClaudeSafetyClassifier on the red-team fixture set
    (tests/test_safety.py), this has strictly better recall (0 misses vs. Claude's
    2/11 adversarial and 2/9 manipulative misses) -- Claude judges each message in
    isolation and is more lenient on single ambiguous statements without a
    established pattern. So it's always run as the deterministic floor in
    EnsembleSafetyClassifier below, never fully replaced by the LLM (see TASKS.md
    T6.1).
    """

    def classify_pre_screen(self, conversation_text: str) -> SafetyDecision:
        text = conversation_text.lower()
        for pattern in _SELF_HARM_PATTERNS:
            if re.search(pattern, text):
                return SafetyDecision("escalate", f"self-harm indicator matched: {pattern!r}")
        for pattern in _MINOR_PATTERNS:
            if re.search(pattern, text):
                return SafetyDecision("block", f"possible-minor indicator matched: {pattern!r}")
        for pattern in _COERCION_PATTERNS:
            if re.search(pattern, text):
                return SafetyDecision("block", f"coercion/abuse indicator matched: {pattern!r}")
        return SafetyDecision("allow", "no red-flag patterns matched")

    def classify_post_gate(self, draft_reply: str) -> SafetyDecision:
        text = draft_reply.lower()
        for pattern in _MANIPULATION_PATTERNS:
            if re.search(pattern, text):
                return SafetyDecision("block", f"manipulation pattern matched: {pattern!r}")
        return SafetyDecision("allow", "no manipulation patterns matched")


_PRE_SCREEN_SYSTEM_PROMPT = """\
You are a safety classifier for a dating-communication coaching app. Given a
redacted conversation, decide: "allow" (no red flags), "block" (clear red flag:
a participant appears to be a minor, or there are signs of coercion/abuse), or
"escalate" (signs of self-harm or crisis -- needs safety resources, not a
silent block). Respond with ONLY a JSON object: {"decision": "...", "reason": "..."}.
"""

_POST_GATE_SYSTEM_PROMPT = """\
You are a safety classifier reviewing a *draft reply* before it's shown to a
user, in a dating-communication coaching app whose hard rule is: never help
someone manipulate (negging, love-bombing, manufactured scarcity, guilt-
tripping) or pressure/pursue someone past a clear "no". Decide "allow" or
"block". Respond with ONLY a JSON object: {"decision": "...", "reason": "..."}.
"""


class ClaudeSafetyClassifier:
    """Real LLM-based classifier (SAD Phase 8.1 GUARD component). Adds judgment/
    coverage on top of RuleBasedSafetyClassifier via EnsembleSafetyClassifier
    below -- not used standalone, since it has measurably worse recall alone
    (see RuleBasedSafetyClassifier's docstring)."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def _classify(self, system_prompt: str, text: str) -> SafetyDecision:
        parsed = self._client.complete_json(system_prompt, text)
        return SafetyDecision(decision=parsed["decision"], reason=parsed["reason"])

    def classify_pre_screen(self, conversation_text: str) -> SafetyDecision:
        return self._classify(_PRE_SCREEN_SYSTEM_PROMPT, conversation_text)

    def classify_post_gate(self, draft_reply: str) -> SafetyDecision:
        return self._classify(_POST_GATE_SYSTEM_PROMPT, draft_reply)


_SEVERITY = {"allow": 0, "block": 1, "escalate": 2}


class EnsembleSafetyClassifier:
    """Combines the rule-based floor with the LLM classifier: the final decision
    is the more severe of the two, so the LLM can only add coverage the rules
    miss, never soften a decision the deterministic rules already caught.
    """

    def __init__(self, rule_based: SafetyClassifier, llm: SafetyClassifier) -> None:
        self._rule_based = rule_based
        self._llm = llm

    def _combine(
        self, rule_decision: SafetyDecision, llm_decision: SafetyDecision
    ) -> SafetyDecision:
        if _SEVERITY[llm_decision.decision] > _SEVERITY[rule_decision.decision]:
            source, chosen = "llm", llm_decision
        else:
            source, chosen = "rule-based", rule_decision
        return SafetyDecision(decision=chosen.decision, reason=f"[{source}] {chosen.reason}")

    def classify_pre_screen(self, conversation_text: str) -> SafetyDecision:
        rule_decision = self._rule_based.classify_pre_screen(conversation_text)
        llm_decision = self._llm.classify_pre_screen(conversation_text)
        return self._combine(rule_decision, llm_decision)

    def classify_post_gate(self, draft_reply: str) -> SafetyDecision:
        rule_decision = self._rule_based.classify_post_gate(draft_reply)
        llm_decision = self._llm.classify_post_gate(draft_reply)
        return self._combine(rule_decision, llm_decision)


def get_safety_classifier(settings: Settings | None = None) -> SafetyClassifier:
    settings = settings or get_settings()
    rule_based = RuleBasedSafetyClassifier()
    if settings.use_llm_safety_classifier and settings.anthropic_api_key:
        client = LLMClient(api_key=settings.anthropic_api_key, model=settings.safety_model)
        return EnsembleSafetyClassifier(rule_based, ClaudeSafetyClassifier(client))
    return rule_based
