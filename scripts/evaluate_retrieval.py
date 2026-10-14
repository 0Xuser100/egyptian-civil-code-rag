import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"

INDEX_PATH = Path("data/processed/civil_code.faiss")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")
REPORT_PATH = Path("docs/evaluation_report.md")

TOP_K = 5


TEST_CASES = [
    {
        "question": "ما هو سن الرشد؟",
        "expected_article": 44,
    },
    {
        "question": "What is the age of majority?",
        "expected_article": 44,
    },
    {
        "question": "متى يعتبر الشخص فاقدا للتمييز؟",
        "expected_article": 45,
    },
    {
        "question": "What age is a person considered devoid of discretion?",
        "expected_article": 45,
    },
    {
        "question": "ما هي الأهلية الناقصة؟",
        "expected_article": 46,
    },
    {
        "question": "Who has limited legal capacity?",
        "expected_article": 46,
    },
    {
        "question": "متى يعتبر الشخص كامل الأهلية لمباشرة حقوقه المدنية؟",
        "expected_article": 44,
    },
    {
        "question": "متى يكون الشخص غير قادر على مباشرة حقوقه المدنية بسبب فقد التمييز؟",
        "expected_article": 45,
    },
    {
        "question": "ماذا يحدث لمن بلغ سن الرشد وكان سفيها أو ذا غفلة؟",
        "expected_article": 46,
    },
    {
        "question": "What is the legal capacity of a person who has reached majority?",
        "expected_article": 44,
    },
    {
        "question": "ما السن الذي يعتبر فيه الشخص فاقدا للتمييز بسبب صغر السن؟",
        "expected_article": 45,
    },
    {
        "question": "What happens to a person who reaches majority but is a prodigal?",
        "expected_article": 46,
    },
    {
        "question": "What is the age of majority under the Gregorian calendar?",
        "expected_article": 44,
    },
    {
        "question": "ما هو السن المحدد للرشد وفقا للتقويم الميلادي؟",
        "expected_article": 44,
    },
    {
        "question": "من بلغ سن التمييز ولم يبلغ سن الرشد يكون ماذا؟",
        "expected_article": 46,
    },
    {
        "question": "Who has full legal capacity to exercise civil rights?",
        "expected_article": 44,
    },
    {
        "question": "من لم يبلغ السابعة يعتبر فاقدا لماذا؟",
        "expected_article": 45,
    },
    {
        "question": "What is the legal status of a person who has not attained the age of seven?",
        "expected_article": 45,
    },
    {
        "question": "ماذا يسمى الشخص الذي بلغ سن الرشد وكان سفيها؟",
        "expected_article": 46,
    },
    {
        "question": "Does reaching majority automatically give full legal capacity?",
        "expected_article": 44,
    },
]


def main() -> None:
    # --------------------------------------------------
    # Load model
    # --------------------------------------------------

    print("Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )

    # --------------------------------------------------
    # Load FAISS index
    # --------------------------------------------------

    print("Loading FAISS index...")

    index = faiss.read_index(
        str(INDEX_PATH)
    )

    # --------------------------------------------------
    # Load chunks
    # --------------------------------------------------

    print("Loading chunks...")

    with CHUNKS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        chunks = json.load(file)

    # --------------------------------------------------
    # Validate index/chunks
    # --------------------------------------------------

    if index.ntotal != len(chunks):
        raise ValueError(
            f"Mismatch: FAISS has {index.ntotal} vectors "
            f"but chunks file has {len(chunks)} chunks."
        )

    print()
    print("===== RETRIEVAL EVALUATION =====")
    print()
    print(f"Chunks: {len(chunks)}")
    print(f"FAISS vectors: {index.ntotal}")
    print(f"Embedding dimension: {index.d}")
    print(f"Test questions: {len(TEST_CASES)}")

    # --------------------------------------------------
    # Evaluation storage
    # --------------------------------------------------

    results = []

    recall_at_1_hits = 0
    recall_at_5_hits = 0
    reciprocal_ranks = []

    # --------------------------------------------------
    # Run evaluation
    # --------------------------------------------------

    for test_number, test_case in enumerate(
        TEST_CASES,
        start=1,
    ):
        question = test_case["question"]
        expected_article = test_case["expected_article"]

        # Embed question
        query_embedding = model.encode(
            [question],
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        # Search FAISS
        scores, indices = index.search(
            query_embedding,
            TOP_K,
        )

        # Get article numbers
        retrieved_articles = [
            chunks[index_value]["article_number"]
            for index_value in indices[0]
        ]

        # Get chunk IDs
        retrieved_ids = [
            chunks[index_value]["id"]
            for index_value in indices[0]
        ]

        # Get similarity scores
        retrieved_scores = [
            float(score)
            for score in scores[0]
        ]

        # --------------------------------------------------
        # Find correct article rank
        # --------------------------------------------------

        correct_rank = None

        for rank, article_number in enumerate(
            retrieved_articles,
            start=1,
        ):
            if article_number == expected_article:
                correct_rank = rank
                break

        # --------------------------------------------------
        # Recall@1
        # --------------------------------------------------

        top_1_correct = (
            retrieved_articles[0] == expected_article
        )

        # --------------------------------------------------
        # Recall@5
        # --------------------------------------------------

        top_5_correct = (
            expected_article in retrieved_articles
        )

        # --------------------------------------------------
        # Count hits
        # --------------------------------------------------

        if top_1_correct:
            recall_at_1_hits += 1

        if top_5_correct:
            recall_at_5_hits += 1

        # --------------------------------------------------
        # Reciprocal Rank
        # --------------------------------------------------

        if correct_rank is not None:
            reciprocal_rank = 1.0 / correct_rank
        else:
            reciprocal_rank = 0.0

        reciprocal_ranks.append(
            reciprocal_rank
        )

        # --------------------------------------------------
        # Store result
        # --------------------------------------------------

        results.append(
            {
                "test_number": test_number,
                "question": question,
                "expected_article": expected_article,
                "retrieved_articles": retrieved_articles,
                "retrieved_ids": retrieved_ids,
                "scores": retrieved_scores,
                "correct_article_rank": correct_rank,
                "top_1_correct": top_1_correct,
                "top_5_correct": top_5_correct,
                "reciprocal_rank": reciprocal_rank,
            }
        )

        # --------------------------------------------------
        # Print result
        # --------------------------------------------------

        print()
        print(f"Test {test_number}")
        print(f"Question: {question}")
        print(
            f"Expected article: {expected_article}"
        )
        print(
            f"Retrieved: {retrieved_articles}"
        )

        if correct_rank is not None:
            print(
                f"Correct article rank: {correct_rank}"
            )
        else:
            print(
                "Correct article rank: NOT FOUND"
            )

        print(
            f"Top-1 correct: {top_1_correct}"
        )

        print(
            f"Top-5 correct: {top_5_correct}"
        )

    # --------------------------------------------------
    # Calculate final metrics
    # --------------------------------------------------

    total_questions = len(TEST_CASES)

    recall_at_1 = (
        recall_at_1_hits
        / total_questions
    )

    recall_at_5 = (
        recall_at_5_hits
        / total_questions
    )

    mrr = (
        sum(reciprocal_ranks)
        / total_questions
    )

    # --------------------------------------------------
    # Print metrics
    # --------------------------------------------------

    print()
    print("=" * 50)
    print("           RETRIEVAL METRICS")
    print("=" * 50)

    print(
        f"Total test questions: {total_questions}"
    )

    print(
        f"Recall@1:             {recall_at_1:.2%}"
    )

    print(
        f"Recall@5:             {recall_at_5:.2%}"
    )

    print(
        f"MRR:                  {mrr:.4f}"
    )

    print("=" * 50)

    # --------------------------------------------------
    # Build Markdown report
    # --------------------------------------------------

    report_lines = [
        "# Retrieval Evaluation Report",
        "",
        "## Evaluation Setup",
        "",
        f"- Embedding model: `{MODEL_NAME}`",
        "- Device: CPU",
        f"- Top-K: {TOP_K}",
        f"- Total test questions: {total_questions}",
        "",
        "## Dataset",
        "",
        f"- Total chunks: {len(chunks)}",
        f"- FAISS vectors: {index.ntotal}",
        f"- Embedding dimension: {index.d}",
        "",
        "## Metrics",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Recall@1 | {recall_at_1:.2%} |",
        f"| Recall@5 | {recall_at_5:.2%} |",
        f"| MRR | {mrr:.4f} |",
        "",
        "## Test Results",
        "",
        "| # | Question | Expected | Retrieved Top-5 | Rank |",
        "|---:|---|---:|---|---:|",
    ]

    # --------------------------------------------------
    # Add test results to Markdown
    # --------------------------------------------------

    for result in results:
        question = result["question"].replace(
            "|",
            "\\|",
        )

        retrieved = ", ".join(
            str(article)
            for article in result[
                "retrieved_articles"
            ]
        )

        rank = result[
            "correct_article_rank"
        ]

        rank_text = (
            str(rank)
            if rank is not None
            else "Not found"
        )

        report_lines.append(
            f"| {result['test_number']} "
            f"| {question} "
            f"| {result['expected_article']} "
            f"| {retrieved} "
            f"| {rank_text} |"
        )

    # --------------------------------------------------
    # Add interpretation
    # --------------------------------------------------

    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The retrieval system uses BGE-M3 "
                "embeddings with a FAISS inner-product "
                "index over normalized embeddings."
            ),
            "",
            (
                "Recall@1 measures whether the expected "
                "article was retrieved as the first result."
            ),
            "",
            (
                "Recall@5 measures whether the expected "
                "article appeared anywhere in the top "
                "five results."
            ),
            "",
            (
                "MRR (Mean Reciprocal Rank) measures how "
                "high the correct article appeared in the "
                "ranking."
            ),
            "",
            "## Baseline",
            "",
            (
                "This evaluation is a retrieval baseline "
                "for the current corpus and embedding "
                "configuration."
            ),
        ]
    )

    # --------------------------------------------------
    # Save Markdown report
    # --------------------------------------------------

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print()
    print(
        f"Evaluation report saved to: {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()