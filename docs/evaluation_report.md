# Retrieval Evaluation Report

## Evaluation Setup

- Embedding model: `BAAI/bge-m3`
- Device: CPU
- Top-K: 5
- Total test questions: 20

## Dataset

- Total chunks: 1093
- FAISS vectors: 1093
- Embedding dimension: 1024

## Metrics

| Metric | Result |
|---|---:|
| Recall@1 | 95.00% |
| Recall@5 | 100.00% |
| MRR | 0.9750 |

## Test Results

| # | Question | Expected | Retrieved Top-5 | Rank |
|---:|---|---:|---|---:|
| 1 | ما هو سن الرشد؟ | 44 | 44, 46, 45, 375, 112 | 1 |
| 2 | What is the age of majority? | 44 | 44, 46, 45, 112, 828 | 1 |
| 3 | متى يعتبر الشخص فاقدا للتمييز؟ | 45 | 45, 46, 871, 370, 110 | 1 |
| 4 | What age is a person considered devoid of discretion? | 45 | 45, 46, 110, 112, 44 | 1 |
| 5 | ما هي الأهلية الناقصة؟ | 46 | 46, 47, 119, 777, 6 | 1 |
| 6 | Who has limited legal capacity? | 46 | 46, 47, 186, 48, 45 | 1 |
| 7 | متى يعتبر الشخص كامل الأهلية لمباشرة حقوقه المدنية؟ | 44 | 44, 45, 109, 46, 29 | 1 |
| 8 | متى يكون الشخص غير قادر على مباشرة حقوقه المدنية بسبب فقد التمييز؟ | 45 | 45, 46, 948, 670, 273 | 1 |
| 9 | ماذا يحدث لمن بلغ سن الرشد وكان سفيها أو ذا غفلة؟ | 46 | 46, 44, 45, 173, 112 | 1 |
| 10 | What is the legal capacity of a person who has reached majority? | 44 | 44, 46, 45, 109, 112 | 1 |
| 11 | ما السن الذي يعتبر فيه الشخص فاقدا للتمييز بسبب صغر السن؟ | 45 | 45, 46, 42, 110, 44 | 1 |
| 12 | What happens to a person who reaches majority but is a prodigal? | 46 | 46, 44, 487, 494, 112 | 1 |
| 13 | What is the age of majority under the Gregorian calendar? | 44 | 44, 3, 764, 46, 45 | 1 |
| 14 | ما هو السن المحدد للرشد وفقا للتقويم الميلادي؟ | 44 | 44, 46, 112, 45, 3 | 1 |
| 15 | من بلغ سن التمييز ولم يبلغ سن الرشد يكون ماذا؟ | 46 | 46, 45, 44, 42, 112 | 1 |
| 16 | Who has full legal capacity to exercise civil rights? | 44 | 44, 53, 45, 109, 11 | 1 |
| 17 | من لم يبلغ السابعة يعتبر فاقدا لماذا؟ | 45 | 45, 42, 46, 44, 207 | 1 |
| 18 | What is the legal status of a person who has not attained the age of seven? | 45 | 45, 42, 46, 44, 47 | 1 |
| 19 | ماذا يسمى الشخص الذي بلغ سن الرشد وكان سفيها؟ | 46 | 44, 46, 112, 45, 173 | 2 |
| 20 | Does reaching majority automatically give full legal capacity? | 44 | 44, 828, 46, 518, 53 | 1 |

## Interpretation

The retrieval system uses BGE-M3 embeddings with a FAISS inner-product index over normalized embeddings.

Recall@1 measures whether the expected article was retrieved as the first result.

Recall@5 measures whether the expected article appeared anywhere in the top five results.

MRR (Mean Reciprocal Rank) measures how high the correct article appeared in the ranking.

## Baseline

This evaluation is a retrieval baseline for the current corpus and embedding configuration.