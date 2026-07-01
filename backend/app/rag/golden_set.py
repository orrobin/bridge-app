# Hand-labeled golden set: natural-language question -> expected source_id.
# Shared between tests/test_hybrid_retrieval.py and scripts/run_eval.py so the
# offline eval report and the CI-verified test assertion never drift apart.
GOLDEN_SET: list[tuple[str, str]] = [
    (
        "how can I tell if the person I am texting is losing interest",
        "reading-disinterest-signals",
    ),
    (
        "my match has been giving short replies should I worry theyre not interested anymore",
        "reading-disinterest-signals",
    ),
    (
        "how do I bring up wanting to slow down before we meet in person",
        "boundaries-and-consent-early-dating",
    ),
    (
        "I think my joke came across wrong and now things feel awkward between us",
        "repair-after-miscommunication",
    ),
    (
        "we had an awkward exchange yesterday and I want to smooth things over",
        "repair-after-miscommunication",
    ),
]
