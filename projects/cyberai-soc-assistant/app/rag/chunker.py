#!/usr/bin/env python3
"""
CyberAI SOC Assistant
Document Chunker

Splits loaded documents into smaller chunks
for embedding and vector search.
"""


def chunk_documents(
    documents,
    chunk_size=1000,
    overlap=200
):
    """
    Split documents into overlapping chunks.

    Args:
        documents:
            List of loaded documents

        chunk_size:
            Maximum characters per chunk

        overlap:
            Characters repeated between chunks

    Returns:
        List of document chunks
    """

    chunks = []


    for document in documents:

        content = document["content"]

        metadata = document["metadata"]


        start = 0

        chunk_number = 0


        while start < len(content):

            end = start + chunk_size


            chunk_text = content[start:end]


            chunk_metadata = metadata.copy()

            chunk_metadata["chunk_id"] = chunk_number


            chunks.append(
                {
                    "content": chunk_text,

                    "metadata": chunk_metadata
                }
            )


            chunk_number += 1


            start = end - overlap


    return chunks



if __name__ == "__main__":

    from loader import scan_documents


    documents = scan_documents(
        "data/documents/redteam-kb"
    )


    chunks = chunk_documents(
        documents
    )


    print()
    print("=" * 50)

    print(
        f"Documents loaded: {len(documents)}"
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    print("=" * 50)


    print("\nExample chunk metadata:")

    print(
        chunks[0]["metadata"]
    )


    print("\nExample chunk preview:")

    print(
        chunks[0]["content"][:300]
    )


