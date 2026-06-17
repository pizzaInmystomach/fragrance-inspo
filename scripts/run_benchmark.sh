#!/usr/bin/env bash

set -euo pipefail

BRANCH_NAME="${1:-main}"
ENDPOINT="${2:-http://127.0.0.1:8000/api/recommendations}"
REPEATS="${3:-1}"
GOLDEN_PATH="${4:-data/golden_dataset.jsonl}"
SUMMARY_PATH="${5:-metrics/evaluation_summary-main.json}"
CATALOG_PATH="${6:-data/fra_cleaned_with_id.csv}"
METRICS_ENDPOINT="${7:-http://127.0.0.1:8000/metrics/latest}"

# switch between retrieval-only benchmarking and full benchmarking (which includes descriptions and other metadata in the response)
BENCHMARK_SLEEP_SECONDS="${BENCHMARK_SLEEP_SECONDS:-0}"
BENCHMARK_RETRIEVAL_ONLY="${BENCHMARK_RETRIEVAL_ONLY:-true}"
BENCHMARK_INCLUDE_DESCRIPTIONS="${BENCHMARK_INCLUDE_DESCRIPTIONS:-false}"

SAFE_BRANCH_NAME="${BRANCH_NAME%%/*}"
SAFE_BRANCH_NAME=$(printf '%s' "$SAFE_BRANCH_NAME" | sed 's#[^A-Za-z0-9._-]#-#g')
OUT_PATH="metrics/fragrance_request_metrics-${SAFE_BRANCH_NAME}.jsonl"
PARTIAL_OUT_PATH="${OUT_PATH}.partial"

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

[[ -f "$GOLDEN_PATH" ]] || {
  echo "Error: golden dataset not found: $GOLDEN_PATH" >&2
  exit 1
}

[[ -f "scripts/evaluate_retrieval.py" ]] || {
  echo "Error: evaluator not found: scripts/evaluate_retrieval.py" >&2
  exit 1
}

[[ -f "scripts/normalize_main_benchmark_response.py" ]] || {
  echo "Error: response normalizer not found." >&2
  exit 1
}

[[ -f "$CATALOG_PATH" ]] || {
  echo "Error: fragrance catalog not found: $CATALOG_PATH" >&2
  exit 1
}

[[ "$REPEATS" =~ ^[1-9][0-9]*$ ]] || {
  echo "Error: repeats must be a positive integer." >&2
  exit 1
}

[[ "$BENCHMARK_SLEEP_SECONDS" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
  echo "Error: BENCHMARK_SLEEP_SECONDS must be a non-negative number." >&2
  exit 1
}

case "$BENCHMARK_RETRIEVAL_ONLY" in
  true|false) ;;
  *)
    echo "Error: BENCHMARK_RETRIEVAL_ONLY must be true or false." >&2
    exit 1
    ;;
esac

case "$BENCHMARK_INCLUDE_DESCRIPTIONS" in
  true|false) ;;
  *)
    echo "Error: BENCHMARK_INCLUDE_DESCRIPTIONS must be true or false." >&2
    exit 1
    ;;
esac

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

mkdir -p metrics

if [[ "${BENCHMARK_RESET:-0}" == "1" ]]; then
  rm -f "$OUT_PATH" "$PARTIAL_OUT_PATH"
elif [[ -f "$OUT_PATH" && ! -f "$PARTIAL_OUT_PATH" ]]; then
  cp "$OUT_PATH" "$PARTIAL_OUT_PATH"
fi

touch "$PARTIAL_OUT_PATH"

curl --silent --show-error --fail-with-body \
  --connect-timeout 5 \
  --max-time 10 \
  "${ENDPOINT%/api/recommendations}/health" >/dev/null || {
    echo "Error: API is not healthy at ${ENDPOINT%/api/recommendations}/health" >&2
    echo "Start the main API before running the benchmark." >&2
    exit 1
  }

echo "Benchmark branch: $BRANCH_NAME"
echo "Endpoint: $ENDPOINT"
echo "Repeats: $REPEATS"
echo "Golden dataset: $GOLDEN_PATH"
echo "Catalog: $CATALOG_PATH"
echo "Output: $OUT_PATH"
echo "Progress file: $PARTIAL_OUT_PATH"
echo "Summary: $SUMMARY_PATH"
echo "Retrieval only: $BENCHMARK_RETRIEVAL_ONLY"
echo "Include descriptions: $BENCHMARK_INCLUDE_DESCRIPTIONS"
echo "Sleep after each completed request: ${BENCHMARK_SLEEP_SECONDS}s"
echo ""

for run_index in $(seq 1 "$REPEATS"); do
  echo "=== Run $run_index / $REPEATS ==="

  while IFS= read -r row || [[ -n "$row" ]]; do
    [[ -z "${row//[[:space:]]/}" ]] && continue

    query_id=$(jq -r '.query_id' <<<"$row")
    query=$(jq -r '.query' <<<"$row")
    query_type=$(jq -r '.query_type' <<<"$row")

    if jq -e \
      --arg query_id "$query_id" \
      --argjson run_index "$run_index" \
      'select(.query_id == $query_id and .run_index == $run_index)' \
      "$PARTIAL_OUT_PATH" >/dev/null; then
      echo "Skipping $query_id [$query_type], already completed."
      continue
    fi

    echo "Running $query_id [$query_type]..."

    payload=$(jq -cn \
      --arg query "$query" \
      --argjson include_descriptions "$BENCHMARK_INCLUDE_DESCRIPTIONS" \
      --argjson benchmark_retrieval_only "$BENCHMARK_RETRIEVAL_ONLY" \
      '{
        user_input: $query,
        num_recommendations: 5,
        include_descriptions: $include_descriptions,
        benchmark_retrieval_only: $benchmark_retrieval_only
      }'
    )

    response=$(curl --silent --show-error --fail-with-body \
      --connect-timeout 5 \
      --max-time 600 \
      --request POST "$ENDPOINT" \
      -H "Content-Type: application/json" \
      -d "$payload"
    )

    jq -e '
      (.recommendations | type == "array")
      and (.recommendations | length > 0)
    ' <<<"$response" >/dev/null || {
      echo "Error: invalid API response for $query_id" >&2
      printf '%s\n' "$response" >&2
      exit 1
    }

    latest_metrics=$(curl --silent --show-error --fail-with-body \
      --retry 2 \
      --retry-delay 1 \
      --retry-all-errors \
      --connect-timeout 5 \
      --max-time 30 \
      "$METRICS_ENDPOINT"
    )

    jq -e \
      --arg query "$query" \
      '(.prompt == $query) and (.metrics | type == "object")' \
      <<<"$latest_metrics" >/dev/null || {
        echo "Error: latest metrics do not match $query_id" >&2
        printf '%s\n' "$latest_metrics" >&2
        exit 1
      }

    normalized_response=$(
      jq -cn \
        --argjson response "$response" \
        --argjson latest_metrics "$latest_metrics" \
        '{response: $response, latest_metrics: $latest_metrics}' |
        "$PYTHON" scripts/normalize_main_benchmark_response.py \
          --catalog "$CATALOG_PATH"
    )

    jq -c \
      --arg branch "$BRANCH_NAME" \
      --arg query_id "$query_id" \
      --arg query "$query" \
      --arg query_type "$query_type" \
      --argjson run_index "$run_index" \
      '. + {
        branch: $branch,
        query_id: $query_id,
        query: $query,
        query_type: $query_type,
        run_index: $run_index
      }' <<<"$normalized_response" >> "$PARTIAL_OUT_PATH"

    if [[ "$BENCHMARK_SLEEP_SECONDS" != "0" ]]; then
      echo "Sleeping ${BENCHMARK_SLEEP_SECONDS}s..."
      sleep "$BENCHMARK_SLEEP_SECONDS"
    fi

  done < "$GOLDEN_PATH"
done

mv "$PARTIAL_OUT_PATH" "$OUT_PATH"

echo ""
echo "Evaluating retrieval results..."
"$PYTHON" scripts/evaluate_retrieval.py \
  --golden "$GOLDEN_PATH" \
  --results "$OUT_PATH" \
  --output "$SUMMARY_PATH"

echo ""
echo "Done."
echo "Saved to $OUT_PATH"
echo "Summary saved to $SUMMARY_PATH"
