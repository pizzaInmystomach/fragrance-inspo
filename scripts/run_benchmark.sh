#!/usr/bin/env bash

set -euo pipefail

BRANCH_NAME="${1:-feature/local-hybrid-rag}"
ENDPOINT="${2:-http://127.0.0.1:8000/api/recommend}"
REPEATS="${3:-1}"
GOLDEN_PATH="${4:-data/golden_dataset.jsonl}"
SUMMARY_PATH="${5:-metrics/evaluation_summary.json}"

SAFE_BRANCH_NAME="${BRANCH_NAME%%/*}"
SAFE_BRANCH_NAME=$(printf '%s' "$SAFE_BRANCH_NAME" | sed 's#[^A-Za-z0-9._-]#-#g')
OUT_PATH="metrics/fragrance_request_metrics-${SAFE_BRANCH_NAME}.jsonl"
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

[[ -f "$GOLDEN_PATH" ]] || {
  echo "Error: golden dataset not found: $GOLDEN_PATH" >&2
  exit 1
}

[[ -f "scripts/evaluate_retrieval.py" ]] || {
  echo "Error: evaluator not found: scripts/evaluate_retrieval.py" >&2
  exit 1
}

[[ "$REPEATS" =~ ^[1-9][0-9]*$ ]] || {
  echo "Error: repeats must be a positive integer." >&2
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

mkdir -p metrics
rm -f "$TMP_OUT_PATH"
trap 'rm -f "$TMP_OUT_PATH"' EXIT

echo "Benchmark branch: $BRANCH_NAME"
echo "Endpoint: $ENDPOINT"
echo "Repeats: $REPEATS"
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
      '{
        query_id: $query_id,
        prompt: $query,
        top_k: 5,
        return_metrics: true,
        return_retrieval_debug: true
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

    jq -e '
      (.recommendations | type == "array")
      and (.metrics | type == "object")
      and (.retrieval_debug.retrieved_ids | type == "array")
    ' <<<"$response" >/dev/null || {
      echo "Error: invalid API response for $query_id" >&2
      printf '%s\n' "$response" >&2
      exit 1
    }

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
      }' <<<"$response" >> "$TMP_OUT_PATH"

  done < "$GOLDEN_PATH"
done

mv "$TMP_OUT_PATH" "$OUT_PATH"
trap - EXIT

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
