#!/usr/bin/env python3
"""
CyberAI SOC Assistant
Interactive Analyst Chat Interface

Connects:

chat.py
    |
    +--> search.py
    |        |
    |        +--> Qdrant Vector Database
    |
    +--> generator.py
             |
             +--> Ollama Hermes LLM


Provides a terminal-based SOC analyst assistant.
"""


from pathlib import Path
import sys


# --------------------------------------------------
# Import local RAG modules
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

sys.path.append(
    str(BASE_DIR)
)


from search import search
from generator import generate_response



# --------------------------------------------------
# Banner
# --------------------------------------------------

BANNER = """

============================================================
              CyberAI SOC Assistant
              Local Security Knowledge AI

              Qdrant + Ollama Hermes
============================================================

Ask cybersecurity questions.

Examples:

- How does Sherlock perform username discovery?
- Explain OSINT investigation workflow
- What is the purpose of Maigret?
- How can I analyze suspicious activity?

Type 'exit' to quit.

============================================================

"""



# --------------------------------------------------
# Display retrieved sources
# --------------------------------------------------

def display_sources(results):

    print("\n")
    print("=" * 60)
    print("Retrieved Security Knowledge")
    print("=" * 60)


    for index, result in enumerate(
        results,
        start=1
    ):


        payload = result.get(
            "payload",
            {}
        )


        print()


        print(
            f"[{index}] "
            f"{payload.get('filename','unknown')}"
        )


        print(
            "Source:",
            payload.get(
                "source",
                "unknown"
            )
        )


        print(
            "Category:",
            payload.get(
                "category",
                "unknown"
            )
        )


        print(
            "Security Domain:",
            payload.get(
                "security_domain",
                "unknown"
            )
        )


        print(
            "Document Type:",
            payload.get(
                "document_type",
                "unknown"
            )
        )


        print(
            "Score:",
            round(
                result.get(
                    "score",
                    0
                ),
                4
            )
        )


        print(
            "-" * 60
        )



# --------------------------------------------------
# Main Chat Loop
# --------------------------------------------------

def chat():


    print(
        BANNER
    )


    while True:


        try:

            question = input(
                "\nSOC Analyst > "
            )


        except KeyboardInterrupt:

            print(
                "\n\nExiting CyberAI..."
            )

            break



        if question.lower() in [
            "exit",
            "quit",
            "q"
        ]:


            print(
                "\nClosing CyberAI SOC Assistant..."
            )

            break



        if not question.strip():

            continue



        print()


        print(
            "[*] Searching security knowledge base..."
        )



        # Retrieve relevant documents

        results = search(
            question,
            limit=5
        )



        if not results:


            print(
                "\n[!] No relevant documents found."
            )

            continue



        display_sources(
            results
        )



        print()


        print(
            "[*] Generating analyst response..."
        )



        answer = generate_response(
            question,
            results
        )



        print()

        print(
            "=" * 60
        )

        print(
            "CyberAI Analyst Response"
        )

        print(
            "=" * 60
        )


        print()


        print(
            answer
        )



# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    chat()
