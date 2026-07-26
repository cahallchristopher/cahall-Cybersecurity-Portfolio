#!/usr/bin/env python3
"""
CyberAI SOC Assistant
Embedding Generator

Creates, saves, and loads vector embeddings
using Ollama.
"""

import json
from pathlib import Path
import requests


from loader import scan_documents
from chunker import chunk_documents



OLLAMA_URL = "http://localhost:11434/api/embeddings"

EMBEDDING_MODEL = "mxbai-embed-large:latest"


EMBEDDING_FILE = Path(
    "data/embeddings/cyberai_embeddings.json"
)



def generate_embedding(text, retries=3):
    """
    Generate embedding vector using Ollama.
    """

    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text,
    }


    for attempt in range(retries):

        try:

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=180
            )


            response.raise_for_status()


            return response.json()["embedding"]


        except Exception as error:

            print(
                f"[!] Embedding failed "
                f"(attempt {attempt + 1}/{retries})"
            )

            print(
                f"    Error: {error}"
            )


    return None




def embed_documents(chunks):
    """
    Generate embeddings for chunks.
    """

    embedded_documents = []


    total = len(chunks)


    print(
        f"[*] Generating embeddings for {total} chunks"
    )


    for index, chunk in enumerate(chunks):


        vector = generate_embedding(
            chunk["content"]
        )


        if vector is None:

            print(
                f"[!] Skipping chunk {index}"
            )

            print(
                chunk["metadata"]
            )

            continue



        embedded_documents.append(
            {
                "content": chunk["content"],

                "metadata": chunk["metadata"],

                "embedding": vector,
            }
        )



        if index % 10 == 0:

            print(
                f"[+] Processed {index}/{total}"
            )



    return embedded_documents




def save_embeddings(embeddings):
    """
    Save embeddings to disk.
    """

    EMBEDDING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        EMBEDDING_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embeddings,
            file
        )


    print()

    print(
        f"[+] Saved embeddings:"
    )

    print(
        EMBEDDING_FILE
    )





def load_embeddings():
    """
    Load saved embeddings from disk.
    """

    if not EMBEDDING_FILE.exists():

        print(
            "[!] No saved embeddings found"
        )

        return None



    with open(
        EMBEDDING_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        embeddings = json.load(
            file
        )


    print(
        f"[+] Loaded {len(embeddings)} embeddings"
    )


    return embeddings





if __name__ == "__main__":


    existing = load_embeddings()


    if existing:

        print()

        print(
            "Using existing embeddings"
        )

        print(
            f"Vectors: {len(existing)}"
        )

        print(
            "Dimensions:",
            len(
                existing[0]["embedding"]
            )
        )


    else:


        documents = scan_documents(
            "data/documents/redteam-kb"
        )


        chunks = chunk_documents(
            documents
        )


        embeddings = embed_documents(
            chunks
        )


        save_embeddings(
            embeddings
        )


        print()

        print("=" * 50)

        print(
            f"Embeddings created: {len(embeddings)}"
        )

        print("=" * 50)


        if embeddings:

            print()

            print(
                "Vector dimensions:",
                len(
                    embeddings[0]["embedding"]
                )
            )
