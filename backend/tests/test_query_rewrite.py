from app.rag.query_rewrite import rewrite_query


def test_rewrite_adds_salient_terms_from_context():
    context = ["Jordan: no way, how was the ramen"]
    rewritten = rewrite_query("is she into me?", context)

    assert "ramen" in rewritten.lower()
    assert "is she into me?" in rewritten


def test_rewrite_does_not_duplicate_terms_already_in_question():
    context = ["Alex: I love hiking on weekends"]
    rewritten = rewrite_query("should I ask about hiking?", context)

    assert rewritten.lower().count("hiking") == 1


def test_rewrite_with_no_context_returns_question_unchanged():
    assert rewrite_query("is she into me?", []) == "is she into me?"
