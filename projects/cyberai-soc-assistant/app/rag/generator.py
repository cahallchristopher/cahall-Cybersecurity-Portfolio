#!/usr/bin/env python3
"""
CyberAI SOC Assistant
LLM Response Generator

Uses retrieved cybersecurity context
and generates SOC analyst responses
using Ollama.
"""


import requests



# ==============================
# Configuration
# ==============================

OLLAMA_URL = (
    "http://localhost:11434/api/generate"
)


MODEL = (
    "nous-hermes2:10.7b"
)



# ==============================
# Generate SOC Response
# ==============================

def generate_response(
    question,
    context
):
    """
    Generate an analyst response
    using retrieved RAG context.
    """



    prompt = f"""
You are CyberAI, a cybersecurity SOC analyst assistant.

Your role is to analyze security information and provide
clear, accurate, evidence-based responses.

Use ONLY the provided knowledge context.

If the information is not available in the context,
state that clearly.

Structure your response as:

1. Summary
2. Technical Details
3. Relevant Tools or Techniques
4. Analyst Recommendations


Security Knowledge Context:
--------------------------------

{context}

--------------------------------

User Question:

{question}


SOC Analyst Response:
"""



    payload = {

        "model": MODEL,


        "prompt": prompt,


        "stream": False,


        "options": {

            # More deterministic answers
            "temperature": 0.2,


            # Larger context window
            "num_ctx": 8192
        }
    }



    try:

        response = requests.post(

            OLLAMA_URL,

            json=payload,

            timeout=300

        )


        response.raise_for_status()



        result = response.json()



        return result.get(

            "response",

            "No response generated."

        )



    except requests.exceptions.RequestException as error:


        return (

            f"[!] Ollama API error: {error}"

        )



# ==============================
# Test
# ==============================

if __name__ == "__main__":


    sample_context = """
Sherlock is an OSINT tool used to search
for usernames across many online platforms.

Maigret is an OSINT tool that collects
information associated with usernames,
including profiles and related metadata.
"""



    question = (

        "Explain how Sherlock and Maigret "
        "are used during an OSINT investigation."

    )



    answer = generate_response(

        question,

        sample_context

    )



    print()

    print("=" * 60)

    print(answer)

    print("=" * 60)
