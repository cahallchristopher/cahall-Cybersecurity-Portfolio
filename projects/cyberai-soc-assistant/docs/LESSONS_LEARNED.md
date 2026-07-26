# Lessons Learned

---

## Build the Pipeline in Order

Each module depends on the previous one.
Trying to test search before embeddings exist just fails.
The correct order is: loader --> chunker --> embeddings --> vectorstore --> search --> generator --> chat.
Running each module standalone (__main__ block) confirms it works before moving on.

---

## Save Embeddings to Disk

Generating embeddings is expensive -- tens of minutes for a large knowledge base.
Saving to JSON means you only do it once.
The load_embeddings() function checks for the file first.
This pattern is essential for iterative development.

---

## Garbage In, Garbage Out

The first version of search returned AI prompt files as top results.
The documents themselves were the problem -- not the search logic.
Adding source filtering fixed it immediately.
Always inspect what documents are actually in your knowledge base before debugging search quality.

---

## Re-Ranking Matters More Than Raw Similarity

COSINE similarity alone is not enough.
A README about Sherlock is more valuable than a Python script mentioning Sherlock in a comment.
The boost system adds domain knowledge about document quality on top of raw vector similarity.
This significantly improved response quality.

---

## Temperature 0.2 for SOC Responses

Higher temperature (0.7+) produces creative answers but not accurate ones.
SOC analyst responses need to be precise and evidence-based.
0.2 keeps the LLM grounded in the retrieved context.

---

## Overlapping Chunks Prevent Lost Context

Without overlap, a sentence split across two chunks loses meaning.
With overlap=200, the same 200 characters appear in both chunks.
This ensures no piece of important information is cut off at a boundary.

---

## Batch Uploads Are Not Optional

Qdrant has payload size limits.
Uploading 1000+ vectors in one request fails silently or throws a 413.
Always batch. 100 per batch works reliably.

---

## Hard Blocks vs Soft Penalties

Some files should never appear in results (AI prompts, templates).
Others are just lower priority (Python source vs documentation).
Hard blocks remove them entirely.
Soft penalties let them appear only if nothing better is available.
Both are needed.
