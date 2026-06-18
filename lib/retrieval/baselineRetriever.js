const fs = require("fs");
const path = require("path");

const DATA_PATH = path.join(process.cwd(), "data", "fra_cleaned_with_id.csv");
const ACCORD_COLUMNS = ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"];
const STOP_WORDS = new Set([
  "about", "after", "before", "can", "find", "fragrance", "looking", "need",
  "notes", "perfume", "please", "recommend", "scent", "something", "that",
  "this", "want", "with", "would",
]);
const FIELD_WEIGHTS = [
  ["accords", 4],
  ["top_notes", 3],
  ["middle_notes", 3],
  ["base_notes", 3],
  ["name", 2.5],
  ["brand", 1.5],
  ["description", 1],
];

let cachedRows = null;

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

function tokenize(value) {
  return String(value || "")
    .toLowerCase()
    .match(/[a-z0-9]+(?:-[a-z0-9]+)?|[\u4e00-\u9fff]+/g) || [];
}

function counts(tokens) {
  return tokens.reduce((acc, token) => {
    acc[token] = (acc[token] || 0) + 1;
    return acc;
  }, {});
}

function splitList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function loadRows() {
  if (cachedRows) return cachedRows;

  const text = fs.readFileSync(DATA_PATH, "utf8").replace(/^\uFEFF/, "");
  const [headerLine, ...lines] = text.split(/\r?\n/).filter(Boolean);
  const headers = parseCsvLine(headerLine);
  cachedRows = lines.map((line) => {
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] || ""]));
    const accords = ACCORD_COLUMNS.map((column) => row[column]).filter(Boolean);
    return {
      id: row.id,
      name: row.Perfume,
      brand: row.Brand,
      url: row.url,
      accords,
      top_notes: splitList(row.Top),
      middle_notes: splitList(row.Middle),
      base_notes: splitList(row.Base),
      description: [...accords, row.Top, row.Middle, row.Base].filter(Boolean).join(" "),
    };
  }).filter((row) => row.id);
  return cachedRows;
}

function scoreRow(row, queryCounts) {
  return FIELD_WEIGHTS.reduce((score, [field, weight]) => {
    const fieldCounts = counts(tokenize(row[field]));
    return score + Object.entries(queryCounts).reduce(
      (sum, [term, count]) => sum + weight * Math.min(count, fieldCounts[term] || 0),
      0,
    );
  }, 0);
}

async function baselineRetrieve({ query, topK = 5 }) {
  const startedAt = performance.now();
  const rows = loadRows();
  const queryCounts = counts(tokenize(query).filter((term) => !STOP_WORDS.has(term)));
  const results = rows
    .map((row, index) => ({ row, index, score: scoreRow(row, queryCounts) }))
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, topK)
    .map((item) => item.row);
  const retrievedIds = results.map((result) => result.id);
  const baselineMs = performance.now() - startedAt;

  return {
    results,
    retrievedIds,
    metrics: {
      retrieval_total_ms: Number(baselineMs.toFixed(2)),
      baseline_ms: Number(baselineMs.toFixed(2)),
    },
    debug: {
      baseline_top_ids: retrievedIds,
    },
  };
}

module.exports = { baselineRetrieve };
