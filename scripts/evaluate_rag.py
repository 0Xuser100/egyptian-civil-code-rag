
import json
import re
import time
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import ollama
from sentence_transformers import SentenceTransformer

# ============================================================
# Configuration
# ============================================================

EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:3b"

INDEX_PATH = Path("data/processed/civil_code.faiss")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")

REPORT_JSON_PATH = Path("data/processed/rag_evaluation.json")
REPORT_MD_PATH = Path("docs/rag_evaluation.md")

TOP_K = 5


# ============================================================
# Evaluation Dataset
# ============================================================

TEST_CASES = [
    {
        "id": 1,
        "question": "ما هو سن الرشد؟",
        "expected_articles": [44],
        "reference_answer": "سن الرشد هو إحدى وعشرون سنة ميلادية كاملة.",
        "answerable": True,
        "key_facts": ["21", "سنة", "الرشد"],
    },
    {
        "id": 2,
        "question": "What is the age of majority?",
        "expected_articles": [44],
        "reference_answer": (
            "The age of majority is twenty one years completed "
            "according to the Gregorian calendar."
        ),
        "answerable": True,
        "key_facts": ["21", "majority"],
    },
    {
        "id": 3,
        "question": "متى يعتبر الشخص فاقدا للتمييز؟",
        "expected_articles": [45],
        "reference_answer": (
            "يعتبر من لم يبلغ السابعة فاقدا للتمييز، "
            "كما يكون فاقد التمييز بسبب صغر السن أو العته أو الجنون."
        ),
        "answerable": True,
        "key_facts": ["7", "فاقد", "التمييز"],
    },
    {
        "id": 4,
        "question": "What age is a person considered devoid of discretion?",
        "expected_articles": [45],
        "reference_answer": (
            "A person who has not attained the age of seven "
            "is considered devoid of discretion."
        ),
        "answerable": True,
        "key_facts": ["7", "discretion"],
    },
    {
        "id": 5,
        "question": "ما هي الأهلية الناقصة؟",
        "expected_articles": [46],
        "reference_answer": (
            "تكون الأهلية ناقصة لمن بلغ سن التمييز ولم يبلغ سن الرشد، "
            "وكذلك لمن بلغ سن الرشد وكان سفيها أو ذا غفلة."
        ),
        "answerable": True,
        "key_facts": ["الأهلية", "ناقصة"],
    },
    {
        "id": 6,
        "question": "Who has limited legal capacity?",
        "expected_articles": [46],
        "reference_answer": (
            "A person who has reached the age of discretion but has not "
            "attained majority, and a person who has attained majority "
            "but is a prodigal or an imbecile."
        ),
        "answerable": True,
        "key_facts": ["limited", "capacity"],
    },
    {
        "id": 7,
        "question": "متى يعتبر الشخص كامل الأهلية لمباشرة حقوقه المدنية؟",
        "expected_articles": [44],
        "reference_answer": (
            "عندما يبلغ الشخص سن الرشد متمتعا بقواه العقلية "
            "ولم يحجر عليه."
        ),
        "answerable": True,
        "key_facts": ["الرشد", "قواه العقلية", "كامل الأهلية"],
    },
    {
        "id": 8,
        "question": "متى يكون الشخص غير قادر على مباشرة حقوقه المدنية بسبب فقد التمييز؟",
        "expected_articles": [45],
        "reference_answer": (
            "إذا كان فاقد التمييز لصغر في السن أو عته أو جنون."
        ),
        "answerable": True,
        "key_facts": ["فاقد", "التمييز"],
    },
    {
        "id": 9,
        "question": "ماذا يحدث لمن بلغ سن الرشد وكان سفيها أو ذا غفلة؟",
        "expected_articles": [46],
        "reference_answer": (
            "يكون ناقص الأهلية وفقا لما يقرره القانون."
        ),
        "answerable": True,
        "key_facts": ["ناقص الأهلية", "سفيها", "غفلة"],
    },
    {
        "id": 10,
        "question": "What is the legal capacity of a person who has reached majority?",
        "expected_articles": [44],
        "reference_answer": (
            "A person who has reached majority, possesses their mental "
            "faculties, and is not under legal disability has full legal "
            "capacity to exercise civil rights."
        ),
        "answerable": True,
        "key_facts": ["full", "legal capacity", "majority"],
    },
    {
        "id": 11,
        "question": "ما السن الذي يعتبر فيه الشخص فاقدا للتمييز بسبب صغر السن؟",
        "expected_articles": [45],
        "reference_answer": (
            "من لم يبلغ السابعة يعتبر فاقدا للتمييز."
        ),
        "answerable": True,
        "key_facts": ["7", "فاقدا للتمييز"],
    },
    {
        "id": 12,
        "question": "What happens to a person who reaches majority but is a prodigal?",
        "expected_articles": [46],
        "reference_answer": (
            "The person has limited legal capacity according to the law."
        ),
        "answerable": True,
        "key_facts": ["limited", "capacity"],
    },
    {
        "id": 13,
        "question": "What is the age of majority under the Gregorian calendar?",
        "expected_articles": [44],
        "reference_answer": (
            "The age of majority is twenty one years completed "
            "according to the Gregorian calendar."
        ),
        "answerable": True,
        "key_facts": ["21", "Gregorian"],
    },
    {
        "id": 14,
        "question": "ما هو السن المحدد للرشد وفقا للتقويم الميلادي؟",
        "expected_articles": [44],
        "reference_answer": (
            "سن الرشد هو إحدى وعشرون سنة ميلادية كاملة."
        ),
        "answerable": True,
        "key_facts": ["21", "ميلادية"],
    },
    {
        "id": 15,
        "question": "من بلغ سن التمييز ولم يبلغ سن الرشد يكون ماذا؟",
        "expected_articles": [46],
        "reference_answer": (
            "يكون ناقص الأهلية وفقا لما يقرره القانون."
        ),
        "answerable": True,
        "key_facts": ["ناقص الأهلية"],
    },
    {
        "id": 16,
        "question": "Who has full legal capacity to exercise civil rights?",
        "expected_articles": [44],
        "reference_answer": (
            "A person who has reached majority, possesses their mental "
            "faculties, and is not under legal disability."
        ),
        "answerable": True,
        "key_facts": ["full legal capacity"],
    },
    {
        "id": 17,
        "question": "من لم يبلغ السابعة يعتبر فاقدا لماذا؟",
        "expected_articles": [45],
        "reference_answer": (
            "يعتبر فاقدا للتمييز."
        ),
        "answerable": True,
        "key_facts": ["7", "فاقدا للتمييز"],
    },
    {
        "id": 18,
        "question": (
            "What is the legal status of a person who has not "
            "attained the age of seven?"
        ),
        "expected_articles": [45],
        "reference_answer": (
            "A person who has not attained the age of seven "
            "is considered devoid of discretion."
        ),
        "answerable": True,
        "key_facts": ["7", "devoid of discretion"],
    },
    {
        "id": 19,
        "question": "ماذا يسمى الشخص الذي بلغ سن الرشد وكان سفيها؟",
        "expected_articles": [46],
        "reference_answer": (
            "يكون ناقص الأهلية وفقا لما يقرره القانون."
        ),
        "answerable": True,
        "key_facts": ["ناقص الأهلية", "سفيها"],
    },
    {
        "id": 20,
        "question": "Does reaching majority automatically give full legal capacity?",
        "expected_articles": [44],
        "reference_answer": (
            "Not necessarily. The person must have reached majority, "
            "possess their mental faculties, and not be under legal disability."
        ),
        "answerable": True,
        "key_facts": ["majority", "mental faculties", "legal disability"],
    },
    {
        "id": 21,
        "question": "ما هي عقوبة السرقة في قانون العقوبات المصري؟",
        "expected_articles": [],
        "reference_answer": "",
        "answerable": False,
        "key_facts": [],
    },
    {
        "id": 22,
        "question": "What is the prison sentence for murder under Egyptian law?",
        "expected_articles": [],
        "reference_answer": "",
        "answerable": False,
        "key_facts": [],
    },
    {
        "id": 23,
        "question": "ما هي ضريبة الدخل المستحقة على الموظف؟",
        "expected_articles": [],
        "reference_answer": "",
        "answerable": False,
        "key_facts": [],
    },
    {
        "id": 24,
        "question": "What is the current price of gold in Egypt?",
        "expected_articles": [],
        "reference_answer": "",
        "answerable": False,
        "key_facts": [],
    },
    {
        "id": 25,
        "question": "ما هو رقم هاتف المحكمة المختصة؟",
        "expected_articles": [],
        "reference_answer": "",
        "answerable": False,
        "key_facts": [],
    },
]


# ============================================================
# Retrieval
# ============================================================

def retrieve_articles(
    question: str,
    embedding_model: SentenceTransformer,
    index: faiss.Index,
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    query_embedding = embedding_model.encode(
        [question],
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32",
    )

    scores, indices = index.search(
        query_embedding,
        TOP_K,
    )

    results = []

    for score, index_position in zip(scores[0], indices[0]):
        if index_position < 0:
            continue

        chunk = chunks[index_position]

        results.append(
            {
                "score": float(score),
                "article_number": chunk["article_number"],
                "id": chunk["id"],
                "text_ar": chunk["text_ar"],
                "text_en": chunk["text_en"],
            }
        )

    return results


# ============================================================
# Context Construction
# ============================================================

def build_context(results: list[dict[str, Any]]) -> str:
    context_parts = []

    for result in results:
        context_parts.append(
            
                f"Article {result['article_number']}\n\n"
                f"Arabic:\n{result['text_ar']}\n\n"
                f"English:\n{result['text_en']}"
            
        )

    return "\n\n---\n\n".join(context_parts)


# ============================================================
# LLM Generation
# ============================================================

SYSTEM_PROMPT = """
You are a legal RAG assistant for the Egyptian Civil Code.

Answer ONLY from the provided context.

Rules:
1. Do not use outside knowledge.
2. Do not guess or invent facts.
3. Do not invent legal rules, penalties, dates, or numbers.
4. If the context does not contain enough information, clearly say that
   the answer cannot be determined from the provided articles.
5. If the answer is supported, mention the relevant Article number.
6. Keep the answer concise.
"""


def generate_answer(
    question: str,
    context: str,
) -> tuple[str, float]:
    prompt = f"""
Context:
{context}

Question:
{question}
"""

    start_time = time.perf_counter()

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    latency = time.perf_counter() - start_time
    answer = response["message"]["content"].strip()

    return answer, latency


# ============================================================
# Normalization
# ============================================================

ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.translate(ARABIC_DIGITS)

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# Citation Extraction
# ============================================================

def extract_article_numbers(answer: str) -> list[int]:
    normalized = answer.translate(ARABIC_DIGITS)

    patterns = [
        r"article\s*(\d+)",
        r"art\.\s*(\d+)",
        r"المادة\s*\(?\s*(\d+)",
        r"مادة\s*\(?\s*(\d+)",
    ]

    numbers: set[int] = set()

    for pattern in patterns:
        matches = re.findall(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        )

        for match in matches:
            numbers.add(int(match))

    return sorted(numbers)


# ============================================================
# Abstention
# ============================================================

ABSTENTION_PATTERNS = [
    "cannot be determined",
    "cannot determine",
    "not provided",
    "not available",
    "insufficient information",
    "cannot answer",
    "لا يمكن تحديد",
    "لا يمكن الإجابة",
    "لا يمكن معرفة",
    "غير كافية",
    "غير متوفرة",
    "لا تتضمن",
    "لا يحتوي",
    "لا تحتوي",
]


def is_abstention(answer: str) -> bool:
    normalized = normalize_text(answer)

    return any(
        normalize_text(pattern) in normalized
        for pattern in ABSTENTION_PATTERNS
    )


# ============================================================
# Retrieval Metrics
# ============================================================

def retrieval_hit(
    retrieved_articles: list[dict[str, Any]],
    expected_articles: list[int],
) -> bool:
    retrieved_numbers = {
        article["article_number"]
        for article in retrieved_articles
    }

    return bool(
        retrieved_numbers.intersection(expected_articles)
    )


# ============================================================
# Citation Metric
# ============================================================

def citation_correct(
    answer: str,
    expected_articles: list[int],
) -> bool:
    if not expected_articles:
        return True

    cited_articles = set(
        extract_article_numbers(answer)
    )

    return bool(
        cited_articles.intersection(expected_articles)
    )


# ============================================================
# Reference Answer Signal
# ============================================================

def key_fact_matches(
    answer: str,
    key_facts: list[str],
) -> list[str]:
    normalized_answer = normalize_text(answer)

    matched = []

    for fact in key_facts:
        if normalize_text(fact) in normalized_answer:
            matched.append(fact)

    return matched


def answer_correctness_signal(
    answer: str,
    key_facts: list[str],
    answerable: bool,
) -> float:
    if not answerable:
        return 1.0 if is_abstention(answer) else 0.0

    if not key_facts:
        return 0.0

    matched = key_fact_matches(
        answer,
        key_facts,
    )

    return len(matched) / len(key_facts)


# ============================================================
# Grounding Signal
# ============================================================

def extract_numeric_facts(text: str) -> set[str]:
    normalized = text.translate(ARABIC_DIGITS)

    numbers = re.findall(
        r"\b\d+(?:\.\d+)?\b",
        normalized,
    )

    return set(numbers)


def unsupported_numbers(
    answer: str,
    context: str,
) -> list[str]:
    answer_numbers = extract_numeric_facts(answer)
    context_numbers = extract_numeric_facts(context)

    return sorted(
        answer_numbers - context_numbers
    )


# ============================================================
# Main Evaluation
# ============================================================

def main() -> None:
    print("=" * 60)
    print("             RAG EVALUATION")
    print("=" * 60)

    print("\nLoading embedding model...")

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )

    print("Loading FAISS index...")

    index = faiss.read_index(
        str(INDEX_PATH)
    )

    with CHUNKS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        chunks = json.load(file)

    results = []

    for case in TEST_CASES:
        print(
            f"\n[{case['id']}/{len(TEST_CASES)}] "
            f"{case['question']}"
        )

        retrieved = retrieve_articles(
            case["question"],
            embedding_model,
            index,
            chunks,
        )

        context = build_context(retrieved)

        answer, latency = generate_answer(
            case["question"],
            context,
        )

        hit = retrieval_hit(
            retrieved,
            case["expected_articles"],
        )

        citation_ok = citation_correct(
            answer,
            case["expected_articles"],
        )

        abstained = is_abstention(answer)

        matched_facts = key_fact_matches(
            answer,
            case["key_facts"],
        )

        correctness = answer_correctness_signal(
            answer,
            case["key_facts"],
            case["answerable"],
        )

        unsupported = unsupported_numbers(
            answer,
            context,
        )

        abstention_correct = (
            abstained
            if not case["answerable"]
            else True
        )

        result = {
            "id": case["id"],
            "question": case["question"],
            "answerable": case["answerable"],
            "expected_articles": case["expected_articles"],
            "retrieved_articles": [
                {
                    "article_number": item["article_number"],
                    "score": item["score"],
                }
                for item in retrieved
            ],
            "answer": answer,
            "latency_seconds": round(
                latency,
                3,
            ),
            "retrieval_hit": hit,
            "citation_correct": citation_ok,
            "matched_key_facts": matched_facts,
            "answer_correctness_signal": round(
                correctness,
                3,
            ),
            "abstained": abstained,
            "abstention_correct": abstention_correct,
            "unsupported_numbers": unsupported,
        }

        results.append(result)

        print(f"  Retrieval hit: {hit}")
        print(f"  Citation correct: {citation_ok}")
        print(
            "  Answer correctness signal: "
            f"{correctness:.2f}"
        )
        print(f"  Abstained: {abstained}")
        print(
            "  Unsupported numbers: "
            f"{unsupported}"
        )
        print(f"  Latency: {latency:.2f}s")

    # ========================================================
    # Aggregate Metrics
    # ========================================================

    answerable_results = [
        result
        for result in results
        if result["answerable"]
    ]

    unanswerable_results = [
        result
        for result in results
        if not result["answerable"]
    ]

    retrieval_recall = (
        sum(
            result["retrieval_hit"]
            for result in answerable_results
        )
        / len(answerable_results)
    )

    citation_accuracy = (
        sum(
            result["citation_correct"]
            for result in answerable_results
        )
        / len(answerable_results)
    )

    mean_correctness = (
        sum(
            result["answer_correctness_signal"]
            for result in answerable_results
        )
        / len(answerable_results)
    )

    abstention_accuracy = (
        sum(
            result["abstention_correct"]
            for result in unanswerable_results
        )
        / len(unanswerable_results)
    )

    unsupported_number_cases = sum(
        bool(result["unsupported_numbers"])
        for result in answerable_results
    )

    unsupported_number_rate = (
        unsupported_number_cases
        / len(answerable_results)
    )

    mean_latency = (
        sum(
            result["latency_seconds"]
            for result in results
        )
        / len(results)
    )

    metrics = {
        "total_questions": len(results),
        "answerable_questions": len(
            answerable_results
        ),
        "unanswerable_questions": len(
            unanswerable_results
        ),
        "retrieval_recall": round(
            retrieval_recall,
            4,
        ),
        "citation_accuracy": round(
            citation_accuracy,
            4,
        ),
        "mean_answer_correctness_signal": round(
            mean_correctness,
            4,
        ),
        "abstention_accuracy": round(
            abstention_accuracy,
            4,
        ),
        "unsupported_number_rate": round(
            unsupported_number_rate,
            4,
        ),
        "mean_latency_seconds": round(
            mean_latency,
            4,
        ),
    }

    report = {
        "configuration": {
            "embedding_model": EMBEDDING_MODEL,
            "llm_model": LLM_MODEL,
            "top_k": TOP_K,
        },
        "metrics": metrics,
        "results": results,
    }

    # ========================================================
    # Save JSON
    # ========================================================

    with REPORT_JSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # Save Markdown
    # ========================================================

    markdown = f"""# RAG Evaluation Report

## Configuration

- Embedding model: `{EMBEDDING_MODEL}`
- LLM: `{LLM_MODEL}`
- Top-K: `{TOP_K}`
- Test cases: `{len(results)}`

## Metrics

| Metric | Score |
|---|---:|
| Retrieval Recall | {retrieval_recall:.2%} |
| Citation Accuracy | {citation_accuracy:.2%} |
| Mean Answer Correctness Signal | {mean_correctness:.2%} |
| Abstention Accuracy | {abstention_accuracy:.2%} |
| Unsupported Number Rate | {unsupported_number_rate:.2%} |
| Mean Latency | {mean_latency:.2f}s |

## Metric Interpretation

### Retrieval Recall

Measures whether at least one expected article appears
within the top-{TOP_K} retrieved articles.

### Citation Accuracy

Measures whether the generated answer explicitly cites
one of the expected articles.

### Answer Correctness Signal

Measures the proportion of predefined key facts found
in the generated answer.

This is an automatic signal, not a semantic judge.

### Abstention Accuracy

Measures whether the model correctly refuses to answer
questions that are outside the provided Civil Code context.

### Unsupported Number Rate

Measures how often an answerable response contains a
numeric value that does not appear in the retrieved context.

This is only a warning signal and **must not be interpreted
as a complete hallucination detector**.

### Hallucination Evaluation

A reliable hallucination rate cannot be established from
numeric matching alone. Legal hallucination evaluation
requires claim-level semantic checking or human review.

## Detailed Results

| ID | Answerable | Retrieval | Citation | Correctness | Abstained | Unsupported Numbers | Latency |
|---:|---|---|---|---:|---|---|---:|
"""

    for result in results:
        markdown += (
            f"| {result['id']} "
            f"| {result['answerable']} "
            f"| {result['retrieval_hit']} "
            f"| {result['citation_correct']} "
            f"| {result['answer_correctness_signal']:.2f} "
            f"| {result['abstained']} "
            f"| {result['unsupported_numbers']} "
            f"| {result['latency_seconds']:.2f}s |\n"
        )

    markdown += "\n## Answers\n\n"

    for result in results:
        markdown += (
            f"### {result['id']}. "
            f"{result['question']}\n\n"
            f"**Answer:**\n\n"
            f"{result['answer']}\n\n"
            f"**Expected articles:** "
            f"{result['expected_articles']}\n\n"
            f"**Retrieved articles:** "
            f"{result['retrieved_articles']}\n\n"
            f"**Matched key facts:** "
            f"{result['matched_key_facts']}\n\n"
            f"**Unsupported numbers:** "
            f"{result['unsupported_numbers']}\n\n"
            "---\n\n"
        )

    with REPORT_MD_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(markdown)

    # ========================================================
    # Console Summary
    # ========================================================

    print("\n")
    print("=" * 60)
    print("              RAG EVALUATION SUMMARY")
    print("=" * 60)

    print(
        f"Retrieval Recall:             "
        f"{retrieval_recall:.2%}"
    )

    print(
        f"Citation Accuracy:            "
        f"{citation_accuracy:.2%}"
    )

    print(
        f"Mean Answer Correctness:      "
        f"{mean_correctness:.2%}"
    )

    print(
        f"Abstention Accuracy:          "
        f"{abstention_accuracy:.2%}"
    )

    print(
        f"Unsupported Number Rate:      "
        f"{unsupported_number_rate:.2%}"
    )

    print(
        f"Mean Latency:                 "
        f"{mean_latency:.2f}s"
    )

    print("=" * 60)

    print(
        f"\nJSON report: {REPORT_JSON_PATH}"
    )

    print(
        f"Markdown report: {REPORT_MD_PATH}"
    )


if __name__ == "__main__":
    main()
