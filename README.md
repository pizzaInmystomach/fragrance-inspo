# Fragrance Inspo Hybrid RAG

> A forked fragrance recommendation system focused on **retrieval indexing**, **Hybrid RAG**, and **experiment-driven evaluation**.

Fragrance Inspo Hybrid RAG 是從原本分組開發的香水推薦專案 fork 下來後，針對 **retrieval / indexing strategy** 重新設計與實驗比較的系統。

原始專案的核心目標是：根據使用者輸入的香氣需求，推薦合適的香水。
本 fork 的重點不是單純增加 UI 或 prompt，而是把推薦流程拆成可測量、可比較、可切換的實驗系統，主要比較：

1. **Baseline Retrieval**：傳統 keyword / rule-based weighted matching
2. **Hybrid Retrieval**：BM25 + HNSW Vector Search + Reciprocal Rank Fusion
3. **Local LLM vs Cloud LLM**：比較本地生成與雲端生成在品質、延遲與成本上的差異

---

## Table of Contents

* [Project Motivation](#project-motivation)
* [System Overview](#system-overview)
* [Retrieval Methods](#retrieval-methods)
* [Experiment Design](#experiment-design)
* [Benchmark Results](#benchmark-results)
* [Analysis](#analysis)
* [Project Structure](#project-structure)
* [Tech Stack](#tech-stack)
* [Setup](#setup)
* [Usage](#usage)
* [Environment Variables](#environment-variables)
* [API Example](#api-example)
* [Limitations](#limitations)
* [Future Work](#future-work)
* [License](#license)

---

## Project Motivation

原本的香水推薦系統可以完成「使用者輸入需求 → 產生推薦」的基本流程，但在推薦系統中，真正決定結果品質的通常不是 LLM 本身，而是：

* 系統能不能先找到正確候選香水
* 候選資料是否包含 query 需要的香調、accords、notes
* retrieval 是否能同時處理「明確 note」與「抽象氛圍」需求
* end-to-end latency 是否能接受
* local model 是否真的划算，或只是把 API cost 變成等待時間

因此，本 fork 將專案改造成一個可比較的 RAG 實驗系統，重點放在：

* 建立可重複實驗的 golden dataset
* 實作 baseline 與 hybrid retrieval
* 量化 retrieval quality
* 量化 end-to-end performance
* 分析 local / cloud LLM 的實際 trade-off

---

## System Overview

整體流程如下：

```text
User Query
   |
   v
Retrieval Mode Switch
   |
   +-------------------------+
   |                         |
   v                         v
Baseline Retriever      Hybrid Retriever
Keyword Matching        BM25 + HNSW + RRF
   |                         |
   +-----------+-------------+
               |
               v
        Top-K Candidate Fragrances
               |
               v
       LLM Generation Mode Switch
               |
       +-------+--------+
       |                |
       v                v
   Local LLM        Cloud LLM
   Ollama           Groq / LangChain
       |                |
       +-------+--------+
               |
               v
     Final 3 Fragrance Recommendations
               |
               v
       Metrics + Debug Output
```

The system supports two benchmark modes:

| Mode             | Purpose                                      |
| ---------------- | -------------------------------------------- |
| `retrieval_only` | Evaluate retrieval quality without LLM noise |
| `e2e`            | Evaluate the full recommendation pipeline    |

---

## Retrieval Methods

### 1. Baseline Retrieval

Baseline retrieval 使用傳統 rule-based matching。它會將 query tokenized 後，對不同欄位給予不同權重：

| Field          | Weight |
| -------------- | -----: |
| `accords`      |    4.0 |
| `top_notes`    |    3.0 |
| `middle_notes` |    3.0 |
| `base_notes`   |    3.0 |
| `name`         |    2.5 |
| `brand`        |    1.5 |
| `description`  |    1.0 |

Baseline 也加入了少量 synonym expansion，例如：

```text
earthy -> earth, soil, moss, patchouli, vetiver
woody  -> wood, cedar, sandalwood
rainy  -> aquatic, ozonic, mineral
smoky  -> smoke, incense
```

這個方法的優點是可解釋、穩定、對明確 note query 很直接。
缺點是它仍然偏 keyword matching，對抽象語意例如 *“old book pages in a rainy library”* 這類需求，泛化能力有限。

---

### 2. Hybrid Retrieval

Hybrid retrieval 使用三個核心技術：

| Component            | Role                                            |
| -------------------- | ----------------------------------------------- |
| `BM25`               | Captures exact lexical matches                  |
| `HNSW Vector Search` | Captures semantic similarity through embeddings |
| `RRF`                | Merges sparse and dense retrieval rankings      |

Hybrid pipeline:

```text
Query
 |
 +--> Ollama Embedding: nomic-embed-text
 |
 +--> HNSW Vector Search
 |
 +--> BM25 Full-Text Search
 |
 +--> Reciprocal Rank Fusion
 |
 v
Final Top-K Results
```

The hybrid retriever retrieves candidates from both:

* dense vector search: semantic similarity
* sparse full-text search: exact keyword / note matching

Then it applies **Reciprocal Rank Fusion**:

```text
score(d) = Σ 1 / (k + rank_i(d))
```

This allows the system to keep results that rank well in either semantic search or lexical search.

---

## Experiment Design

### Dataset

The experiment uses a fragrance corpus with around **24,063 fragrance records**.

Each fragrance contains:

* canonical `id`
* perfume name
* brand
* country
* gender
* rating value / rating count
* year
* top notes
* middle notes
* base notes
* main accords
* perfumer metadata

The canonical `id` is preserved across retrieval, golden dataset, benchmark, and final recommendation validation.

---

### Golden Datasets

Two evaluation datasets are used:

| Dataset                       |       Size | Purpose                              |
| ----------------------------- | ---------: | ------------------------------------ |
| `golden_dataset.jsonl`        | 50 queries | Retrieval-only evaluation            |
| `golden_dataset_e2e_20.jsonl` | 20 queries | End-to-end recommendation evaluation |

The retrieval-only dataset evaluates whether the system can retrieve relevant fragrance candidates before any LLM generation happens.

The end-to-end dataset evaluates whether the final generated recommendations contain relevant fragrance IDs.

---

### Metrics

#### Retrieval Quality Metrics

| Metric     | Meaning                                                        |
| ---------- | -------------------------------------------------------------- |
| `Hit@K`    | Whether at least one relevant item appears in top K            |
| `Recall@K` | Fraction of relevant items retrieved in top K                  |
| `MRR`      | Reciprocal rank of the first relevant result                   |
| `nDCG@K`   | Ranking quality with higher weight on earlier relevant results |

#### Latency Metrics

| Metric               | Meaning                         |
| -------------------- | ------------------------------- |
| `embedding_ms`       | Query embedding generation time |
| `baseline_ms`        | Baseline retrieval time         |
| `bm25_ms`            | BM25 search time                |
| `hnsw_ms`            | HNSW vector search time         |
| `rrf_ms`             | Reciprocal Rank Fusion time     |
| `retrieval_total_ms` | Total retrieval latency         |
| `llm_generation_ms`  | LLM generation time             |
| `end_to_end_ms`      | Full request latency            |

#### Cost Metrics

For cloud LLM experiments, token-based cost estimates are recorded.

For local LLM experiments, external API cost is avoided, but latency and local compute cost still exist. In short: local LLM is not “free”; it just sends the bill to your patience and laptop fan.

---

## Benchmark Results

### Retrieval-only Benchmark

Evaluation size: **50 queries**

| Metric               | Baseline Retrieval | Hybrid Retrieval | Observation                       |
| -------------------- | -----------------: | ---------------: | --------------------------------- |
| `MRR`                |              0.129 |            0.130 | Slight hybrid improvement         |
| `Hit@3`              |              0.160 |            0.140 | Baseline slightly higher          |
| `Hit@5`              |              0.200 |            0.180 | Baseline slightly higher          |
| `Recall@3`           |             0.0477 |           0.0563 | Hybrid better                     |
| `Recall@5`           |             0.0730 |           0.0703 | Similar, baseline slightly higher |
| `nDCG@3`             |             0.0742 |           0.0894 | Hybrid better                     |
| `nDCG@5`             |             0.0848 |           0.0864 | Hybrid slightly better            |
| `retrieval_total_ms` |          507.76 ms |         30.53 ms | Hybrid much faster                |

### Retrieval-only Interpretation

The hybrid retriever does **not** dominate every metric.

The important finding is more nuanced:

* Hybrid improves `Recall@3` and `nDCG@3`
* Baseline remains competitive on `Hit@3` and `Hit@5`
* Hybrid dramatically reduces retrieval latency
* Hybrid retrieves and ranks better when semantic matching helps
* Baseline still performs well when the query directly overlaps with note names or accords

In practical terms:

> Hybrid retrieval is better as a scalable RAG retrieval backbone, but the current configuration still needs tuning to consistently beat baseline on binary hit rate.

This is a real result, not README perfume sprayed on top of mediocre numbers.

---

## End-to-End Benchmark

Evaluation size: **20 queries**

| Configuration        | `Hit@3` | `end_to_end_ms` | `retrieval_total_ms` | `llm_generation_ms` | Estimated Cost / 1000 Queries |
| -------------------- | ------: | --------------: | -------------------: | ------------------: | ----------------------------: |
| Baseline + Cloud LLM |    0.10 |     1,339.22 ms |            529.88 ms |           801.09 ms |                     `$0.0640` |
| Hybrid + Local LLM   |    0.20 |    23,265.13 ms |             36.07 ms |        23,148.02 ms |          `$0.0515` equivalent |
| Hybrid + Cloud LLM   |    0.20 |       815.70 ms |             24.03 ms |           716.82 ms |                     `$0.0507` |

### End-to-End Interpretation

The best overall configuration is:

```text
Hybrid Retrieval + Cloud LLM
```

Why:

* `Hit@3` improves from `0.10` to `0.20`
* end-to-end latency drops from `1339.22 ms` to `815.70 ms`
* retrieval latency drops from `529.88 ms` to `24.03 ms`
* estimated token cost is also lower

The local LLM configuration proves that the system can run without relying on a cloud LLM, but the result is much slower. The bottleneck is no longer retrieval; it becomes local generation.

In other words:

```text
Hybrid retrieval solved the search bottleneck.
Local LLM created a generation bottleneck.
```

---

## Analysis

### 1. Retrieval Indexing Matters

The baseline system scans and scores fragrance rows directly. This is simple and explainable, but slow.

Hybrid retrieval uses indexed search:

* BM25 for lexical match
* HNSW for vector similarity
* RRF for rank fusion

This reduces retrieval latency from hundreds of milliseconds to tens of milliseconds.

---

### 2. Hybrid Retrieval Improves Ranking Quality More Than Binary Hit Rate

Hybrid improves `nDCG@3`, which means relevant results are more likely to appear in better positions when the retrieval succeeds.

However, `Hit@3` and `Hit@5` are slightly lower than baseline in the 50-query retrieval-only benchmark.

This suggests the hybrid system currently has two characteristics:

1. Better ranking when it finds relevant candidates
2. Still misses some queries that baseline catches through exact matching or synonym rules

This is likely caused by:

* embedding semantic drift
* insufficient query expansion
* BM25 tokenization limitations
* RRF parameters not fully tuned
* top-k candidate pool possibly too small before fusion

---

### 3. Local LLM Is Not Automatically Better

Local LLM has the advantage of:

* no external API dependency
* better privacy
* no direct API token cost
* reproducible local environment

But the benchmark shows a major latency penalty.

For this project, local LLM generation dominates end-to-end latency. If the goal is interactive user experience, cloud LLM currently gives better latency.

---

### 4. Retrieval Is No Longer the Main Bottleneck

With hybrid retrieval, retrieval time is around tens of milliseconds.
In the end-to-end pipeline, most latency comes from LLM generation.

Therefore, future optimization should focus on:

* shorter prompt context
* stricter output schema
* smaller / faster generation model
* response caching
* reranking before generation
* reducing candidate context length

---

## Project Structure

See `docs/ARCHITECTURE.md` for the folder ownership rules.

```text
fragrance-inspo/
├── app/
│   ├── api/
│   │   ├── server.py
│   │   └── schemas.py
│   ├── ai/
│   │   └── llm_config.py
│   ├── retrieval/
│   │   ├── baseline_retriever.py
│   │   ├── hybrid_retriever.py
│   │   ├── retrieve.py
│   │   └── common.py
│   ├── csv_loader.py
│   ├── ingest.py
│   ├── schemas.py
│   └── search_engine.py
│
├── data/
│   ├── fra_cleaned.csv
│   ├── fra_cleaned_with_id.csv
│   ├── candidate_pool_for_llm.jsonl
│   ├── golden_dataset.jsonl
│   └── golden_dataset_e2e_20.jsonl
│
├── lancedb_data/
│   └── fragrances.lance/
│
├── docs/
│   └── licenses/
│
├── tests/
│   └── manual/
│
├── main.py                  # compatibility shim for uvicorn main:app
├── metrics/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Tech Stack

| Layer            | Technology             |
| ---------------- | ---------------------- |
| Backend API      | FastAPI                |
| Local LLM        | Ollama                 |
| Local Embedding  | `nomic-embed-text`     |
| Cloud LLM        | Groq via LangChain     |
| Vector Database  | LanceDB                |
| Dense Retrieval  | HNSW                   |
| Sparse Retrieval | BM25 / Tantivy FTS     |
| Rank Fusion      | Reciprocal Rank Fusion |
| Data Format      | CSV, JSONL             |
| Validation       | Pydantic               |
| Containerization | Docker                 |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/pizzaInmystomach/fragrance-inspo.git
cd fragrance-inspo
git checkout feature/local-hybrid-rag
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama models

```bash
ollama pull nomic-embed-text
ollama pull llama3:8b
```

### 5. Build LanceDB index

```bash
python -m app.ingest
```

This step:

1. loads fragrance records from CSV
2. generates embeddings with Ollama
3. writes records into LanceDB
4. builds HNSW vector index
5. builds BM25 full-text index

---

## Run the API

```bash
uvicorn app.api.server:app --host 0.0.0.0 --port 8000
```

`uvicorn main:app` is still supported for backward compatibility.

The API will be available at:

```text
http://localhost:8000
```

---

## Docker Usage

```bash
docker build -t fragrance-inspo-hybrid .
docker run -p 8000:8000 fragrance-inspo-hybrid
```

By default, the Dockerfile points Ollama to:

```text
http://host.docker.internal:11434
```

Make sure Ollama is running on the host machine.

---

## Environment Variables

| Variable                          | Options / Example          | Description                       |
| --------------------------------- | -------------------------- | --------------------------------- |
| `RETRIEVER_MODE`                  | `baseline`, `hybrid`       | Select retrieval method           |
| `LLM_MODE`                        | `local`, `cloud`, `none`   | Select generation mode            |
| `BENCHMARK_MODE`                  | `retrieval_only`, `e2e`    | Select benchmark behavior         |
| `OLLAMA_HOST`                     | `http://localhost:11434`   | Ollama server URL                 |
| `OLLAMA_LLM_MODEL`                | `llama3:8b`                | Local LLM model                   |
| `GROQ_API_KEY`                    | your API key               | Required for cloud LLM            |
| `METRICS_BRANCH`                  | `feature-local-hybrid-rag` | Override metrics branch name      |
| `METRICS_PATH`                    | `metrics/output.jsonl`     | Override metrics output path      |
| `LLM_MAX_ATTEMPTS`                | `3`                        | Max local LLM validation attempts |
| `CLOUD_LLM_MAX_ATTEMPTS`          | `2`                        | Max cloud LLM validation attempts |
| `CLOUD_INPUT_COST_PER_1M_TOKENS`  | `0.05`                     | Cost estimate config              |
| `CLOUD_OUTPUT_COST_PER_1M_TOKENS` | `0.08`                     | Cost estimate config              |

Example:

```bash
export RETRIEVER_MODE=hybrid
export LLM_MODE=cloud
export BENCHMARK_MODE=e2e
export GROQ_API_KEY=your_api_key_here
uvicorn app.api.server:app --host 0.0.0.0 --port 8000
```

---

## API Example

### Normal recommendation request

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "I want a fresh citrus scent that feels like walking through an orange grove on a bright summer morning.",
    "top_k": 5,
    "return_metrics": true,
    "return_retrieval_debug": true
  }'
```

### Retrieval-only benchmark request

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Looking for a clean oceanic perfume with hints of sea salt and mint for hot beach days.",
    "query_id": "q001",
    "top_k": 5,
    "retriever_mode": "hybrid",
    "benchmark_mode": "retrieval_only",
    "llm_mode": "none",
    "return_metrics": true,
    "return_retrieval_debug": true
  }'
```

### Expected response shape

```json
{
  "request_id": "...",
  "timestamp": "...",
  "query_id": "q001",
  "query": "...",
  "experiment_config": {
    "retriever_mode": "hybrid",
    "llm_mode": "none",
    "benchmark_mode": "retrieval_only"
  },
  "metrics": {
    "embedding_ms": 50.42,
    "bm25_ms": 30.16,
    "hnsw_ms": 15.08,
    "rrf_ms": 0.04,
    "retrieval_total_ms": 30.53,
    "end_to_end_ms": 80.94
  },
  "retrieval_debug": {
    "retrieved_ids": ["f000001", "f000002"],
    "bm25_top_ids": [],
    "hnsw_top_ids": [],
    "rrf_top_ids": []
  },
  "recommendations": []
}
```

---

## Reproducibility

To reproduce experiments, keep the following fixed:

* same branch
* same fragrance corpus
* same canonical IDs
* same golden dataset
* same `top_k`
* same retriever mode
* same LLM mode
* same embedding model
* same local hardware or cloud model

Recommended experiment matrix:

| Experiment         | Retriever  | LLM     | Benchmark Mode   |
| ------------------ | ---------- | ------- | ---------------- |
| Retrieval Baseline | `baseline` | `none`  | `retrieval_only` |
| Retrieval Hybrid   | `hybrid`   | `none`  | `retrieval_only` |
| E2E Baseline Cloud | `baseline` | `cloud` | `e2e`            |
| E2E Hybrid Local   | `hybrid`   | `local` | `e2e`            |
| E2E Hybrid Cloud   | `hybrid`   | `cloud` | `e2e`            |

---

## Limitations

1. **Golden dataset size is still small**
   50 retrieval queries and 20 e2e queries are useful for development, but not enough for strong statistical claims.

2. **Fragrance relevance is subjective**
   A query like “rainy library scent” can have multiple valid interpretations.

3. **Hybrid retrieval is not fully tuned**
   RRF `k`, candidate pool size, BM25 fields, embedding text format, and query expansion can still be improved.

4. **Local LLM latency is hardware-dependent**
   Local benchmark numbers depend heavily on machine specs, memory pressure, Ollama model, and quantization.

5. **Cloud LLM results depend on provider latency**
   Cloud experiments may vary by network condition, model availability, rate limits, and provider-side changes.

6. **Cost estimate is token-based**
   It does not include local electricity, hardware cost, or cloud infrastructure beyond token pricing assumptions.

---

## Future Work

* Add a dedicated benchmark runner script
* Export benchmark summaries automatically as JSON / Markdown
* Add query-type analysis, e.g. citrus, floral, woody, gourmand, abstract mood
* Tune RRF parameter and pre-fusion candidate size
* Add reranking stage after hybrid retrieval
* Compare pure BM25, pure HNSW, baseline, and hybrid independently
* Add confidence intervals or bootstrap testing
* Add CI benchmark checks for regression tracking
* Improve dataset documentation and licensing notes
* Add frontend support for showing retrieval debug information

---

## Key Takeaways

1. **Hybrid retrieval substantially reduces retrieval latency.**
2. **Hybrid retrieval improves ranking-oriented metrics such as `nDCG@3`.**
3. **Baseline retrieval remains surprisingly competitive on binary `Hit@K`.**
4. **Hybrid + Cloud LLM gives the best end-to-end trade-off in current experiments.**
5. **Local LLM removes API dependency but creates a major latency bottleneck.**

---


## License

This project source code is licensed under the MIT License. See `LICENSE`.

Third-party dependency licenses are listed in:

- `docs/licenses/THIRD_PARTY_PYTHON_LICENSES.md`
- `docs/licenses/THIRD_PARTY_NODE_LICENSES.md`

Dataset licensing information is listed in:

- `docs/licenses/DATASET_LICENSE.md`
