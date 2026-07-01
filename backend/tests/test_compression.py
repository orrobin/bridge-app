from app.rag.compression import _token_count, compress_context


def test_compression_reduces_token_count_without_dropping_golden_sentence():
    golden_sentence = "Bids for connection are small moments of reaching out to a partner."
    chunk = (
        "This chunk opens with an unrelated sentence about the weather today. "
        f"{golden_sentence} "
        "It then continues with several more unrelated filler sentences to pad it out. "
        "Here is another filler sentence about something else entirely. "
        "And one more filler sentence just to be sure it's long enough to compress."
    )

    query = "what is a bid for connection"
    raw_concat = chunk
    compressed = compress_context([chunk], query)

    assert _token_count(compressed) < _token_count(raw_concat)
    assert golden_sentence in compressed


def test_short_chunk_is_returned_unchanged():
    chunk = "Just one short sentence."
    compressed = compress_context([chunk], "irrelevant query")
    assert compressed == chunk
