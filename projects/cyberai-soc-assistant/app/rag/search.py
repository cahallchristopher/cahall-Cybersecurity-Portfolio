#!/usr/bin/env python3
"""
CyberAI SOC Assistant
RAG Semantic Search Engine

Flow:

User Question
      |
      v
Ollama Embedding Model
      |
      v
Qdrant Vector Search
      |
      v
Document Ranking
      |
      v
Hermes LLM
"""


import requests

from qdrant_client import QdrantClient



# ==================================================
# Configuration
# ==================================================

QDRANT_HOST = "localhost"

QDRANT_PORT = 6333


COLLECTION_NAME = (
    "cyberai_security_kb"
)


OLLAMA_EMBED_URL = (
    "http://localhost:11434/api/embeddings"
)


EMBEDDING_MODEL = (
    "mxbai-embed-large:latest"
)



# ==================================================
# Initialize Qdrant
# ==================================================

client = QdrantClient(

    host=QDRANT_HOST,

    port=QDRANT_PORT

)



# ==================================================
# Generate Query Embedding
# ==================================================

def generate_embedding(text):

    """
    Convert search query into vector.
    """


    if not text.strip():

        raise ValueError(
            "Search query cannot be empty"
        )


    payload = {

        "model": EMBEDDING_MODEL,

        "prompt": text

    }


    response = requests.post(

        OLLAMA_EMBED_URL,

        json=payload,

        timeout=120

    )


    response.raise_for_status()


    return response.json()["embedding"]



# ==================================================
# Document Ranking
# ==================================================

def calculate_boost(metadata):

    """
    Adjust document ranking.

    Higher priority:
        README
        Documentation
        Markdown

    Lower priority:
        AI prompts
        Templates
        Examples
        Source code
    """


    source = metadata.get(

        "source",

        ""

    ).lower()



    boost = 0



    # ----------------------------------
    # Remove prompt contamination
    # ----------------------------------

    blocked_terms = [

        "ai_prompt",

        "prompt.txt",

        "/prompt",

        "template",

        "example",

        "sample"

    ]


    for term in blocked_terms:

        if term in source:

            boost -= 0.50



    # ----------------------------------
    # Documentation priority
    # ----------------------------------

    if "readme" in source:

        boost += 0.15



    if source.endswith(".md"):

        boost += 0.08



    # ----------------------------------
    # Source code reduction
    # ----------------------------------

    if source.endswith(".py"):

        boost -= 0.03



    # ----------------------------------
    # Ignore unnecessary files
    # ----------------------------------

    if "/test" in source:

        boost -= 0.10



    if "__pycache__" in source:

        boost -= 0.25



    return boost



# ==================================================
# Search Qdrant
# ==================================================

def search(

    query,

    limit=8,

    score_threshold=0.65

):

    """
    Perform semantic search.

    Returns ranked security documents.
    """



    print()

    print("[DEBUG SEARCH QUERY]")

    print(query)

    print()



    vector = generate_embedding(

        query

    )



    results = client.query_points(

        collection_name=COLLECTION_NAME,

        query=vector,

        limit=limit * 4,

        with_payload=True

    )



    ranked_results = []



    for point in results.points:


        if point.score < score_threshold:

            continue



        payload = point.payload or {}



        metadata = payload.get(

            "metadata",

            {}

        )


        source = metadata.get(

            "source",

            ""

        ).lower()



        # ----------------------------------
        # Hard block unwanted files
        # ----------------------------------

        blocked_files = [

            "ai_prompt",

            "prompt.txt",

            "template",

            "example"

        ]


        if any(

            item in source

            for item in blocked_files

        ):

            continue



        boost = calculate_boost(

            metadata

        )



        ranked_results.append(

            {

                "score":
                    point.score + boost,


                "original_score":
                    point.score,


                "payload":
                    payload

            }

        )



    ranked_results.sort(

        key=lambda item:

        item["score"],

        reverse=True

    )



    return ranked_results[:limit]



# ==================================================
# Display Results
# ==================================================

def display_results(results):


    print()

    print("=" * 60)

    print(

        f"Results Found: {len(results)}"

    )

    print("=" * 60)



    for index, result in enumerate(

        results,

        start=1

    ):


        payload = result.get(

            "payload",

            {}

        )


        metadata = payload.get(

            "metadata",

            {}

        )


        print()

        print(

            f"[{index}] Score: "

            f"{result['score']:.4f}"

        )


        print(

            "Original Score:",

            f"{result['original_score']:.4f}"

        )


        print(

            "Source:",

            metadata.get(

                "source",

                "unknown"

            )

        )


        print(

            "Category:",

            metadata.get(

                "category",

                "unknown"

            )

        )


        print(

            "Security Domain:",

            metadata.get(

                "security_domain",

                "unknown"

            )

        )


        print()


        content = payload.get(

            "content",

            ""

        )


        print(

            content[:700]

        )


        print("-" * 60)



# ==================================================
# Test Search
# ==================================================

if __name__ == "__main__":


    query = (

        "How can I perform OSINT "
        "username discovery?"
    )



    print()

    print("[*] Query:")

    print(query)



    results = search(

        query,

        limit=8,

        score_threshold=0.65

    )



    display_results(

        results

    )
