# RAG Evaluation Report

## Configuration

- Embedding model: `BAAI/bge-m3`
- LLM: `qwen2.5:3b`
- Top-K: `5`
- Test cases: `25`

## Metrics

| Metric | Score |
|---|---:|
| Retrieval Recall | 100.00% |
| Citation Accuracy | 60.00% |
| Mean Answer Correctness Signal | 74.17% |
| Abstention Accuracy | 80.00% |
| Unsupported Number Rate | 20.00% |
| Mean Latency | 23.34s |

## Metric Interpretation

### Retrieval Recall

Measures whether at least one expected article appears
within the top-5 retrieved articles.

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
| 1 | True | True | True | 1.00 | False | ['21'] | 23.29s |
| 2 | True | True | False | 1.00 | False | ['21'] | 13.19s |
| 3 | True | True | False | 0.33 | False | [] | 18.73s |
| 4 | True | True | False | 0.50 | False | [] | 9.35s |
| 5 | True | True | False | 1.00 | False | [] | 20.82s |
| 6 | True | True | True | 1.00 | False | [] | 10.47s |
| 7 | True | True | True | 0.67 | False | [] | 16.00s |
| 8 | True | True | True | 1.00 | False | [] | 29.88s |
| 9 | True | True | True | 0.00 | False | [] | 29.10s |
| 10 | True | True | True | 1.00 | False | [] | 7.66s |
| 11 | True | True | False | 0.50 | False | [] | 12.15s |
| 12 | True | True | True | 1.00 | False | [] | 18.70s |
| 13 | True | True | False | 1.00 | False | ['21'] | 18.77s |
| 14 | True | True | False | 0.50 | False | ['21'] | 11.87s |
| 15 | True | True | True | 1.00 | False | [] | 24.88s |
| 16 | True | True | True | 1.00 | False | [] | 35.95s |
| 17 | True | True | True | 0.50 | False | [] | 26.64s |
| 18 | True | True | False | 0.50 | False | [] | 6.19s |
| 19 | True | True | True | 1.00 | False | [] | 31.51s |
| 20 | True | True | True | 0.33 | False | [] | 29.52s |
| 21 | False | False | True | 1.00 | True | [] | 42.20s |
| 22 | False | False | True | 1.00 | True | [] | 32.80s |
| 23 | False | False | True | 1.00 | True | [] | 39.44s |
| 24 | False | False | True | 1.00 | True | [] | 28.97s |
| 25 | False | False | True | 0.00 | False | [] | 45.46s |

## Answers

### 1. ما هو سن الرشد؟

**Answer:**

سن الرشد هو 21 سنة حسب Article 44.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6703715920448303}, {'article_number': 46, 'score': 0.500866174697876}, {'article_number': 45, 'score': 0.4626806378364563}, {'article_number': 375, 'score': 0.4407404363155365}, {'article_number': 112, 'score': 0.4387573003768921}]

**Matched key facts:** ['21', 'سنة', 'الرشد']

**Unsupported numbers:** ['21']

---

### 2. What is the age of majority?

**Answer:**

The age of majority is 21 years.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6579602956771851}, {'article_number': 46, 'score': 0.5435848236083984}, {'article_number': 45, 'score': 0.5111317038536072}, {'article_number': 112, 'score': 0.5104308128356934}, {'article_number': 828, 'score': 0.5072574615478516}]

**Matched key facts:** ['21', 'majority']

**Unsupported numbers:** ['21']

---

### 3. متى يعتبر الشخص فاقدا للتمييز؟

**Answer:**

يُعتبر الشخص فاقدا للتمييز إذا لم يبلغ السابعة من العمر.

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6211670637130737}, {'article_number': 46, 'score': 0.5241901874542236}, {'article_number': 871, 'score': 0.5212122201919556}, {'article_number': 370, 'score': 0.49273204803466797}, {'article_number': 110, 'score': 0.4923420250415802}]

**Matched key facts:** ['فاقد']

**Unsupported numbers:** []

---

### 4. What age is a person considered devoid of discretion?

**Answer:**

A person is considered devoid of discretion if they have not attained the age of seven.

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6884241104125977}, {'article_number': 46, 'score': 0.5705739259719849}, {'article_number': 110, 'score': 0.5386026501655579}, {'article_number': 112, 'score': 0.5325524806976318}, {'article_number': 44, 'score': 0.5227688550949097}]

**Matched key facts:** ['discretion']

**Unsupported numbers:** []

---

### 5. ما هي الأهلية الناقصة؟

**Answer:**

الأهلية الناقصة هي المحددة في مادتي 46 و 119 من القانون. يشير المادتان إلى أن الأشخاص الذين لم يبلغوا سن الرشد أو الذين بلغا سن الرشد لكنهم فاقدو أو ناقصو الأهلية، يُعتبرون ناقضين للأهلية وفقًا للقانون.

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 46, 'score': 0.5329146981239319}, {'article_number': 47, 'score': 0.5206155776977539}, {'article_number': 119, 'score': 0.5166704654693604}, {'article_number': 777, 'score': 0.4877402186393738}, {'article_number': 6, 'score': 0.46568772196769714}]

**Matched key facts:** ['الأهلية', 'ناقصة']

**Unsupported numbers:** []

---

### 6. Who has limited legal capacity?

**Answer:**

A person who has reached the age of discretion but has not attained majority and a person who has attained his majority but is a prodigal or an imbecile, has a limited legal capacity according to the provisions of the law.  
(Article 46)

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 46, 'score': 0.6027564406394958}, {'article_number': 47, 'score': 0.5528452396392822}, {'article_number': 186, 'score': 0.5447341203689575}, {'article_number': 48, 'score': 0.539115309715271}, {'article_number': 45, 'score': 0.5329036116600037}]

**Matched key facts:** ['limited', 'capacity']

**Unsupported numbers:** []

---

### 7. متى يعتبر الشخص كامل الأهلية لمباشرة حقوقه المدنية؟

**Answer:**

الشخص يعتبر كامل الأهلية لمباشرة حقوقه المدنية عندما يبلغ سن الرشد، وهو ثمانية وعشرين سنة ميلادية كاملة. يحدد هذا في مادة 44 من القانون.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.684258222579956}, {'article_number': 45, 'score': 0.6117227673530579}, {'article_number': 109, 'score': 0.5621538758277893}, {'article_number': 46, 'score': 0.5607819557189941}, {'article_number': 29, 'score': 0.552777886390686}]

**Matched key facts:** ['الرشد', 'كامل الأهلية']

**Unsupported numbers:** []

---

### 8. متى يكون الشخص غير قادر على مباشرة حقوقه المدنية بسبب فقد التمييز؟

**Answer:**

متى يكون الشخص غير قادر على مباشرة حقوقه المدنية بسبب فقد التمييز؟

منقول من مادتي 45 و46:

فأهلا لمباشرة حقوقه المدنية من كان فاقد التمييز لصغر في السن أو عته أو جنون (Article 45).

وكل من لم يبلغ السابعة يعتبر فاقدا للتمييز. (Article 46).

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6611841917037964}, {'article_number': 46, 'score': 0.5674837827682495}, {'article_number': 948, 'score': 0.508226752281189}, {'article_number': 670, 'score': 0.5054636597633362}, {'article_number': 273, 'score': 0.5009549856185913}]

**Matched key facts:** ['فاقد', 'التمييز']

**Unsupported numbers:** []

---

### 9. ماذا يحدث لمن بلغ سن الرشد وكان سفيها أو ذا غفلة؟

**Answer:**

وفقًا لArticle 45، يتم وصف هذه الحالات كناقصى الأهلية. فلا ي享有 كامل الأهلية ولا يكون ملزما بتعويض الأضرار، ولكنهم لا يعتبرون فاقدى الأهلية كما يظهر في Article 46 حيث يتم وصفهم بأنهم ي享有 أهلية محدودة وفقًا للقانون.

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 46, 'score': 0.6264002323150635}, {'article_number': 44, 'score': 0.6152457594871521}, {'article_number': 45, 'score': 0.5607677698135376}, {'article_number': 173, 'score': 0.521609902381897}, {'article_number': 112, 'score': 0.5130296349525452}]

**Matched key facts:** []

**Unsupported numbers:** []

---

### 10. What is the legal capacity of a person who has reached majority?

**Answer:**

A person who has reached majority has full legal capacity to exercise their civil rights, as per Article 44.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.7175489664077759}, {'article_number': 46, 'score': 0.6482012271881104}, {'article_number': 45, 'score': 0.5673906803131104}, {'article_number': 109, 'score': 0.5634512901306152}, {'article_number': 112, 'score': 0.5630185008049011}]

**Matched key facts:** ['full', 'legal capacity', 'majority']

**Unsupported numbers:** []

---

### 11. ما السن الذي يعتبر فيه الشخص فاقدا للتمييز بسبب صغر السن؟

**Answer:**

الشخص يعتبر فاقدا للتمييز بسبب صغر السن عند الولادة أو قبل الولادة (ماده 45).

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6381579637527466}, {'article_number': 46, 'score': 0.5538482666015625}, {'article_number': 42, 'score': 0.519354522228241}, {'article_number': 110, 'score': 0.5050760507583618}, {'article_number': 44, 'score': 0.5041946768760681}]

**Matched key facts:** ['فاقدا للتمييز']

**Unsupported numbers:** []

---

### 12. What happens to a person who reaches majority but is a prodigal?

**Answer:**

A person who reaches majority but is a prodigal has limited legal capacity according to the provisions of the law (Article 46).

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 46, 'score': 0.5690212249755859}, {'article_number': 44, 'score': 0.5018299221992493}, {'article_number': 487, 'score': 0.500950276851654}, {'article_number': 494, 'score': 0.4903813600540161}, {'article_number': 112, 'score': 0.48711952567100525}]

**Matched key facts:** ['limited', 'capacity']

**Unsupported numbers:** []

---

### 13. What is the age of majority under the Gregorian calendar?

**Answer:**

The age of majority under the Gregorian calendar is 21 years.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6163069009780884}, {'article_number': 3, 'score': 0.5224050879478455}, {'article_number': 764, 'score': 0.4650164842605591}, {'article_number': 46, 'score': 0.4622057378292084}, {'article_number': 45, 'score': 0.45162469148635864}]

**Matched key facts:** ['21', 'Gregorian']

**Unsupported numbers:** ['21']

---

### 14. ما هو السن المحدد للرشد وفقا للتقويم الميلادي؟

**Answer:**

السن المحدد للرشد وفقا للتقويم الميلادي هو 21 سنة كاملة.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6477788686752319}, {'article_number': 46, 'score': 0.4734233617782593}, {'article_number': 112, 'score': 0.47278541326522827}, {'article_number': 45, 'score': 0.47199490666389465}, {'article_number': 3, 'score': 0.4635810852050781}]

**Matched key facts:** ['21']

**Unsupported numbers:** ['21']

---

### 15. من بلغ سن التمييز ولم يبلغ سن الرشد يكون ماذا؟

**Answer:**

من بلغ سن التمييز ولم يبلغ سن الرشد يكون ناقص الأهلية وفقاً لما يقرره القانون. (من Article 46)

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 46, 'score': 0.6859318017959595}, {'article_number': 45, 'score': 0.6459271311759949}, {'article_number': 44, 'score': 0.5822914838790894}, {'article_number': 42, 'score': 0.5100014805793762}, {'article_number': 112, 'score': 0.5023064017295837}]

**Matched key facts:** ['ناقص الأهلية']

**Unsupported numbers:** []

---

### 16. Who has full legal capacity to exercise civil rights?

**Answer:**

All persons attaining majority in possession of their mental faculties and not under legal disability have full legal capacity to exercise their civil rights. (Article 44)

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6056065559387207}, {'article_number': 53, 'score': 0.5451006889343262}, {'article_number': 45, 'score': 0.5398362278938293}, {'article_number': 109, 'score': 0.5312150716781616}, {'article_number': 11, 'score': 0.5236536264419556}]

**Matched key facts:** ['full legal capacity']

**Unsupported numbers:** []

---

### 17. من لم يبلغ السابعة يعتبر فاقدا لماذا؟

**Answer:**

من لم يبلغ السابعة يعتبر فاقدا للتمييز وفقاً للArticle 45.

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6598609685897827}, {'article_number': 42, 'score': 0.5585089921951294}, {'article_number': 46, 'score': 0.5405858755111694}, {'article_number': 44, 'score': 0.5228677988052368}, {'article_number': 207, 'score': 0.5147575736045837}]

**Matched key facts:** ['فاقدا للتمييز']

**Unsupported numbers:** []

---

### 18. What is the legal status of a person who has not attained the age of seven?

**Answer:**

A person who has not attained the age of seven is considered devoid of discretion.

**Expected articles:** [45]

**Retrieved articles:** [{'article_number': 45, 'score': 0.6640945672988892}, {'article_number': 42, 'score': 0.6222236156463623}, {'article_number': 46, 'score': 0.6191282272338867}, {'article_number': 44, 'score': 0.6145487427711487}, {'article_number': 47, 'score': 0.5785350203514099}]

**Matched key facts:** ['devoid of discretion']

**Unsupported numbers:** []

---

### 19. ماذا يسمى الشخص الذي بلغ سن الرشد وكان سفيها؟

**Answer:**

الشخص الذي بلغ سن الرشد وكان سفيهاً يكون ناقص الأهلية وفقاً لما يقرره القانون، وفقاً لArticle 46.

**Expected articles:** [46]

**Retrieved articles:** [{'article_number': 44, 'score': 0.568288266658783}, {'article_number': 46, 'score': 0.5637092590332031}, {'article_number': 112, 'score': 0.48918744921684265}, {'article_number': 45, 'score': 0.4743228554725647}, {'article_number': 173, 'score': 0.44374316930770874}]

**Matched key facts:** ['ناقص الأهلية', 'سفيها']

**Unsupported numbers:** []

---

### 20. Does reaching majority automatically give full legal capacity?

**Answer:**

Yes, reaching majority automatically gives full legal capacity according to Article 44.

**Expected articles:** [44]

**Retrieved articles:** [{'article_number': 44, 'score': 0.6176038980484009}, {'article_number': 828, 'score': 0.5523127317428589}, {'article_number': 46, 'score': 0.5406913757324219}, {'article_number': 518, 'score': 0.5387789011001587}, {'article_number': 53, 'score': 0.527129054069519}]

**Matched key facts:** ['majority']

**Unsupported numbers:** []

---

### 21. ما هي عقوبة السرقة في قانون العقوبات المصري؟

**Answer:**

Article 207 discusses the responsibility of a debtor for loss, but does not address penalties for theft. Therefore, the answer cannot be determined from the provided articles.

**Expected articles:** []

**Retrieved articles:** [{'article_number': 173, 'score': 0.5109524726867676}, {'article_number': 977, 'score': 0.488395094871521}, {'article_number': 172, 'score': 0.47919559478759766}, {'article_number': 207, 'score': 0.474334716796875}, {'article_number': 889, 'score': 0.4642077386379242}]

**Matched key facts:** []

**Unsupported numbers:** []

---

### 22. What is the prison sentence for murder under Egyptian law?

**Answer:**

The provided context does not contain any information regarding prison sentences for murder under Egyptian law. Therefore, the answer cannot be determined from the provided articles.

**Expected articles:** []

**Retrieved articles:** [{'article_number': 21, 'score': 0.4356314539909363}, {'article_number': 25, 'score': 0.4340670704841614}, {'article_number': 14, 'score': 0.4254067540168762}, {'article_number': 11, 'score': 0.4228735566139221}, {'article_number': 874, 'score': 0.4218243360519409}]

**Matched key facts:** []

**Unsupported numbers:** []

---

### 23. ما هي ضريبة الدخل المستحقة على الموظف؟

**Answer:**

cannot be determined from the provided articles.

**Expected articles:** []

**Retrieved articles:** [{'article_number': 684, 'score': 0.5345137119293213}, {'article_number': 691, 'score': 0.5254360437393188}, {'article_number': 683, 'score': 0.5079892873764038}, {'article_number': 1141, 'score': 0.5043578743934631}, {'article_number': 690, 'score': 0.49396976828575134}]

**Matched key facts:** []

**Unsupported numbers:** []

---

### 24. What is the current price of gold in Egypt?

**Answer:**

The current price of gold in Egypt cannot be determined from the provided articles.

**Expected articles:** []

**Retrieved articles:** [{'article_number': 11, 'score': 0.40145987272262573}, {'article_number': 789, 'score': 0.39840003848075867}, {'article_number': 548, 'score': 0.3912409543991089}, {'article_number': 423, 'score': 0.38441941142082214}, {'article_number': 774, 'score': 0.38316941261291504}]

**Matched key facts:** []

**Unsupported numbers:** []

---

### 25. ما هو رقم هاتف المحكمة المختصة؟

**Answer:**

The provided context does not contain any information about phone numbers or the specific court's contact details. 

The relevant article numbers are:
- Article 1089
- Article 1090
- Article 1092
- Article 890
- Article 943

**Expected articles:** []

**Retrieved articles:** [{'article_number': 1089, 'score': 0.5731824636459351}, {'article_number': 1090, 'score': 0.5376108884811401}, {'article_number': 1092, 'score': 0.5211842060089111}, {'article_number': 890, 'score': 0.5193954110145569}, {'article_number': 943, 'score': 0.5131964683532715}]

**Matched key facts:** []

**Unsupported numbers:** []

---

