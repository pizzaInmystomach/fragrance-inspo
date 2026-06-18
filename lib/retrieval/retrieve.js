const { baselineRetrieve } = require("./baselineRetriever");
const { hybridRetrieve } = require("./hybridRetriever");

async function retrieve({ query, topK = 5 }) {
  const mode = (process.env.RETRIEVER_MODE || "hybrid").toLowerCase();
  if (mode === "baseline") {
    return baselineRetrieve({ query, topK });
  }
  if (mode === "hybrid") {
    return hybridRetrieve({ query, topK });
  }
  throw new Error(`Unknown RETRIEVER_MODE=${mode}. Expected "baseline" or "hybrid".`);
}

module.exports = { retrieve };
