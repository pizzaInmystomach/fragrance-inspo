#!/usr/bin/env bash

set -euo pipefail

RETRIEVER_MODE="${RETRIEVER_MODE:-hybrid}"
LLM_MODE="${LLM_MODE:-local}"
BENCHMARK_MODE="${BENCHMARK_MODE:-e2e}"
if [[ "$BENCHMARK_MODE" == "retrieval_only" ]]; then
  LLM_MODE="none"
fi
ENDPOINT="${ENDPOINT:-${1:-http://127.0.0.1:8000/api/recommend}}"
REPEATS="${REPEATS:-${2:-1}}"
TOP_K="${TOP_K:-5}"
CACHE_STATE="${CACHE_STATE:-warm}"
if [[ "$BENCHMARK_MODE" == "e2e" && "$LLM_MODE" == "cloud" ]]; then
  BENCHMARK_SLEEP_SECONDS="${BENCHMARK_SLEEP_SECONDS:-15}"
else
  BENCHMARK_SLEEP_SECONDS="${BENCHMARK_SLEEP_SECONDS:-0}"
fi

if [[ "$BENCHMARK_MODE" == "retrieval_only" ]]; then
  DEFAULT_GOLDEN_PATH="data/golden_dataset.jsonl"
  DEFAULT_OUT_PATH="metrics/retrieval-${RETRIEVER_MODE}-50.jsonl"
  DEFAULT_SUMMARY_PATH="metrics/retrieval-${RETRIEVER_MODE}-summary.json"
else
  DEFAULT_GOLDEN_PATH="data/golden_dataset_e2e_20.jsonl"
  DEFAULT_OUT_PATH="metrics/e2e-${RETRIEVER_MODE}-${LLM_MODE}-20.jsonl"
  DEFAULT_SUMMARY_PATH="metrics/e2e-${RETRIEVER_MODE}-${LLM_MODE}-summary.json"
fi

GOLDEN_PATH="${GOLDEN_PATH:-${3:-$DEFAULT_GOLDEN_PATH}}"
OUT_PATH="${OUT_PATH:-${4:-$DEFAULT_OUT_PATH}}"
SUMMARY_PATH="${SUMMARY_PATH:-${5:-$DEFAULT_SUMMARY_PATH}}"
TMP_OUT_PATH="${OUT_PATH}.tmp.$$"

command -v jq >/dev/null 2>&1 || {
  echo "Error: jq is required." >&2
  exit 1
}

command -v curl >/dev/null 2>&1 || {
  echo "Error: curl is required." >&2
  exit 1
}

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  echo "Error: Python 3 is required." >&2
  exit 1
fi

[[ "$REPEATS" =~ ^[1-9][0-9]*$ ]] || {
  echo "Error: repeats must be a positive integer." >&2
  exit 1
}

[[ "$TOP_K" =~ ^[1-9][0-9]*$ ]] || {
  echo "Error: TOP_K must be a positive integer." >&2
  exit 1
}

[[ "$BENCHMARK_SLEEP_SECONDS" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
  echo "Error: BENCHMARK_SLEEP_SECONDS must be a non-negative number." >&2
  exit 1
}

if [[ "$BENCHMARK_MODE" == "e2e" && ! -f "$GOLDEN_PATH" && "$GOLDEN_PATH" == "data/golden_dataset_e2e_20.jsonl" ]]; then
  "$PYTHON" scripts/create_e2e_subset.py
fi

[[ -f "$GOLDEN_PATH" ]] || {
  echo "Error: golden dataset not found: $GOLDEN_PATH" >&2
  exit 1
}

jq -e -s '
  length > 0
  and all(.[];
    ((.query_id | type) == "string" and (.query_id | length) > 0)
    and ((.query | type) == "string" and (.query | length) > 0)
    and ((.query_type | type) == "string" and (.query_type | length) > 0)
  )
' "$GOLDEN_PATH" >/dev/null || {
  echo "Error: golden dataset contains invalid benchmark rows." >&2
  exit 1
}

mkdir -p "$(dirname "$OUT_PATH")"
rm -f "$TMP_OUT_PATH"
trap 'rm -f "$TMP_OUT_PATH"' EXIT

echo "Retriever mode: $RETRIEVER_MODE"
echo "LLM mode: $LLM_MODE"
echo "Benchmark mode: $BENCHMARK_MODE"
echo "Endpoint: $ENDPOINT"
echo "Repeats: $REPEATS"
echo "Top K: $TOP_K"
echo "Cache state: $CACHE_STATE"
echo "Query sleep seconds: $BENCHMARK_SLEEP_SECONDS"
echo "Golden dataset: $GOLDEN_PATH"
echo "Output: $OUT_PATH"
echo "Summary: $SUMMARY_PATH"
echo ""

for run_index in $(seq 1 "$REPEATS"); do
  echo "=== Run $run_index / $REPEATS ==="

  while IFS= read -r row || [[ -n "$row" ]]; do
    [[ -z "${row//[[:space:]]/}" ]] && continue

    query_id=$(jq -r '.query_id' <<<"$row")
    query=$(jq -r '.query' <<<"$row")
    query_type=$(jq -r '.query_type' <<<"$row")

    echo "Running $query_id [$query_type]..."

    payload=$(jq -cn \
      --arg query_id "$query_id" \
      --arg query "$query" \
      --arg query_type "$query_type" \
      --arg cache_state "$CACHE_STATE" \
      --arg retriever_mode "$RETRIEVER_MODE" \
      --arg llm_mode "$LLM_MODE" \
      --arg benchmark_mode "$BENCHMARK_MODE" \
      --argjson top_k "$TOP_K" \
      --argjson run_index "$run_index" \
      '{
        query_id: $query_id,
        prompt: $query,
        query_type: $query_type,
        top_k: $top_k,
        return_metrics: true,
        return_retrieval_debug: true,
        retriever_mode: $retriever_mode,
        llm_mode: $llm_mode,
        benchmark_mode: $benchmark_mode,
        run_index: $run_index,
        cache_state: $cache_state
      }'
    )

    response=$(curl --silent --show-error --fail-with-body \
      --retry 2 \
      --retry-delay 1 \
      --retry-all-errors \
      --request POST "$ENDPOINT" \
      -H "Content-Type: application/json" \
      -d "$payload"
    )

    jq -e 'type == "object"' <<<"$response" >/dev/null || {
      echo "Error: non-JSON-object API response for $query_id" >&2
      printf '%s\n' "$response" >&2
      exit 1
    }

    jq -e '(.experiment_config | type) == "object"' <<<"$response" >/dev/null || {
      echo "Error: API response missing experiment_config for $query_id; response was not written." >&2
      printf '%s\n' "$response" >&2
      exit 1
    }

    jq -e '
      (.recommendations | type == "array")
      and (.metrics | type == "object")
      and (.retrieval_debug.retrieved_ids | type == "array")
    ' <<<"$response" >/dev/null || {
      echo "Error: invalid API response for $query_id" >&2
      printf '%s\n' "$response" >&2
      exit 1
    }

    jq -e \
      --arg retriever_mode "$RETRIEVER_MODE" \
      --arg llm_mode "$LLM_MODE" \
      --arg benchmark_mode "$BENCHMARK_MODE" \
      '
        .experiment_config.retriever_mode == $retriever_mode
        and .experiment_config.llm_mode == $llm_mode
        and .experiment_config.benchmark_mode == $benchmark_mode
      ' <<<"$response" >/dev/null || {
        echo "Error: API experiment_config does not match requested benchmark config for $query_id" >&2
        printf '%s\n' "$response" >&2
        exit 1
      }

    if [[ "$BENCHMARK_MODE" == "retrieval_only" ]]; then
      jq -e '
        (.metrics.llm_generation_ms == null)
        and (.metrics.input_tokens == null)
        and (.metrics.output_tokens == null)
        and (.metrics.tokens_per_sec == null)
      ' <<<"$response" >/dev/null || {
        echo "Error: retrieval-only response contains LLM metrics for $query_id" >&2
        printf '%s\n' "$response" >&2
        exit 1
      }
    fi

    jq -c \
      --arg query_id "$query_id" \
      --arg query "$query" \
      --arg query_type "$query_type" \
      --arg retriever_mode "$RETRIEVER_MODE" \
      --arg llm_mode "$LLM_MODE" \
      --arg benchmark_mode "$BENCHMARK_MODE" \
      --arg cache_state "$CACHE_STATE" \
      --argjson run_index "$run_index" \
      '. + {
        query_id: $query_id,
        query: $query,
        query_type: $query_type,
        run_index: $run_index,
        cache_state: $cache_state,
        requested_experiment_config: {
          retriever_mode: $retriever_mode,
          llm_mode: $llm_mode,
          benchmark_mode: $benchmark_mode
        }
      }' <<<"$response" >> "$TMP_OUT_PATH"

    if [[ "$BENCHMARK_SLEEP_SECONDS" != "0" && "$BENCHMARK_SLEEP_SECONDS" != "0.0" ]]; then
      echo "Sleeping ${BENCHMARK_SLEEP_SECONDS}s before next query..."
      sleep "$BENCHMARK_SLEEP_SECONDS"
    fi

  done < "$GOLDEN_PATH"
done

mv "$TMP_OUT_PATH" "$OUT_PATH"
trap - EXIT

echo ""
if [[ "$BENCHMARK_MODE" == "retrieval_only" ]]; then
  echo "Evaluating retrieval results..."
  "$PYTHON" scripts/evaluate_retrieval.py \
    --golden "$GOLDEN_PATH" \
    --results "$OUT_PATH" \
    --output "$SUMMARY_PATH"
else
  echo "Evaluating E2E results..."
  "$PYTHON" scripts/evaluate_e2e.py \
    --golden "$GOLDEN_PATH" \
    --results "$OUT_PATH" \
    --output "$SUMMARY_PATH"
fi

echo ""
echo "Done."
echo "Saved to $OUT_PATH"
echo "Summary saved to $SUMMARY_PATH"
