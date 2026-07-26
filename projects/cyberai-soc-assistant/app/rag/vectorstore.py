#!/usr/bin/env python3
"""
CyberAI SOC Assistant
Vector Store Loader

Loads saved embeddings into Qdrant
for semantic search.
"""

import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
)



# ==============================
# Configuration
# ==============================

EMBEDDING_FILE = Path(
    "data/embeddings/cyberai_embeddings.json"
)


QDRANT_HOST = "localhost"

QDRANT_PORT = 6333


COLLECTION_NAME = (
    "cyberai_security_kb"
)


VECTOR_SIZE = 1024



# ==============================
# Load Embeddings
# ==============================

def load_embeddings():
    """
    Load saved embedding vectors.
    """

    if not EMBEDDING_FILE.exists():

        raise FileNotFoundError(
            f"Missing embedding file: {EMBEDDING_FILE}"
        )


    with open(
        EMBEDDING_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        embeddings = json.load(file)


    print(
        f"[+] Loaded {len(embeddings)} embeddings"
    )


    return embeddings



# ==============================
# Qdrant Collection
# ==============================

def create_collection(client):
    """
    Create Qdrant collection if needed.
    """

    collections = [
        collection.name
        for collection in (
            client.get_collections()
            .collections
        )
    ]


    if COLLECTION_NAME in collections:

        print(
            f"[+] Collection already exists: "
            f"{COLLECTION_NAME}"
        )

        return



    client.create_collection(

        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(

            size=VECTOR_SIZE,

            distance=Distance.COSINE
        )
    )


    print(
        f"[+] Created collection: "
        f"{COLLECTION_NAME}"
    )



# ==============================
# Upload Vectors
# ==============================

def upload_vectors(
    client,
    embeddings,
    batch_size=100
):
    """
    Upload embeddings in batches.

    Qdrant limits request size,
    so large uploads are split.
    """

    total = len(embeddings)


    print()

    print(
        f"[*] Uploading {total} vectors"
    )



    for start in range(
        0,
        total,
        batch_size
    ):


        batch = embeddings[
            start:start + batch_size
        ]


        points = []


        for index, item in enumerate(
            batch,
            start=start
        ):


            points.append(

                PointStruct(

                    id=index,


                    vector=item[
                        "embedding"
                    ],


                    payload={

                        "content":
                            item["content"],


                        "metadata":
                            item["metadata"],
                    }
                )
            )



        client.upsert(

            collection_name=COLLECTION_NAME,

            points=points
        )


        completed = min(
            start + batch_size,
            total
        )


        print(
            f"[+] Uploaded "
            f"{completed}/{total}"
        )



    print()

    print(
        "[+] Upload complete"
    )



# ==============================
# Main
# ==============================

if __name__ == "__main__":


    print(
        "[*] Connecting to Qdrant"
    )


    client = QdrantClient(

        host=QDRANT_HOST,

        port=QDRANT_PORT
    )



    embeddings = load_embeddings()



    create_collection(
        client
    )



    upload_vectors(

        client,

        embeddings
    )



    print()

    print("=" * 50)

    print(
        "Vector database ready"
    )

    print("=" * 50)
