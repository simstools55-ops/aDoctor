from doctor.url_identity import assess_url_identity, same_resource_by_trailing_slash, trailing_slash_variant


def test_trailing_slash_variant():
    assert trailing_slash_variant("https://example.com/1238") == "https://example.com/1238/"
    assert trailing_slash_variant("https://example.com/1238/") == "https://example.com/1238"


def test_same_resource_by_trailing_slash():
    assert same_resource_by_trailing_slash("https://example.com/1238", "https://example.com/1238/")
    assert not same_resource_by_trailing_slash("https://example.com/1238", "https://example.com/1239/")


def test_indexed_canonical_prevents_false_index_diagnosis():
    result = assess_url_identity(
        "https://example.com/1238",
        matched_url="https://example.com/1238/",
        canonical_url="https://example.com/1238/",
        indexed_requested=False,
        indexed_matched=True,
    )
    assert result.status == "INDEXED_CANONICAL_CONFIRMED"
    assert result.same_resource is True
    assert result.requires_user_action is False


def test_true_technical_risk_requires_both_candidates_unindexed():
    result = assess_url_identity(
        "https://example.com/1238",
        matched_url="https://example.com/1238/",
        indexed_requested=False,
        indexed_matched=False,
    )
    assert result.status == "SAME_RESOURCE_NORMALIZATION"
    # The slash pair still needs canonical/redirect evidence before declaring a failure.
    assert result.requires_user_action is False


def test_unrelated_unindexed_urls_are_technical_risk():
    result = assess_url_identity(
        "https://example.com/1238",
        matched_url="https://example.com/other",
        indexed_requested=False,
        indexed_matched=False,
    )
    assert result.status == "TECHNICAL_INDEX_RISK"
    assert result.requires_user_action is True
