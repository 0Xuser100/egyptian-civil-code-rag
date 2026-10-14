from rag.pipeline import build_context


def test_build_context_contains_article_information() -> None:
    results = [
        {
            "article_number": 44,
            "text_ar": "يبلغ سن الرشد إحدى وعشرين سنة ميلادية كاملة.",
            "text_en": "The age of majority is twenty-one full Gregorian years.",
        }
    ]

    context = build_context(results)

    assert "Article 44" in context
    assert "يبلغ سن الرشد" in context
    assert "twenty-one" in context