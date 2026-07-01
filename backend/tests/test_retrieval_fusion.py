import uuid

from app.rag.retrieval import reciprocal_rank_fusion


def test_doc_ranked_high_in_both_lists_wins():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    vector_ranking = [a, b, c]
    lexical_ranking = [a, c, b]

    fused = reciprocal_rank_fusion([vector_ranking, lexical_ranking])
    assert fused[0][0] == a


def test_doc_only_in_one_list_still_scores():
    a, b = uuid.uuid4(), uuid.uuid4()
    fused = dict(reciprocal_rank_fusion([[a], []]))
    assert a in fused
    assert b not in fused


def test_consistently_low_ranked_doc_beats_absent_doc():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # c ranks last in both lists but appears in both; b is absent from the second list.
    fused = dict(reciprocal_rank_fusion([[a, b, c], [a, c]]))
    assert fused[c] > fused[b]
