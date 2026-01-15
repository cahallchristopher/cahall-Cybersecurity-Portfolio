#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# -------------------------
# SAFETY
# -------------------------
if os.geteuid() == 0:
    sys.exit("Do not run as root.")

# -------------------------
# CONFIG
# -------------------------
MODEL = "qwen2.5:7b"
MAX_ITERATIONS = 150  # start small

BASE = Path.home() / "resume_agent"
INBOX = BASE / "data" / "inbox"
CHROMA_DIR = BASE / "data" / "chroma"
OUTDIR = BASE / "outputs"

RESUME = INBOX / "resume.txt"
JOB = INBOX / "job.txt"
RULES = INBOX / "resume_rules.txt"

# -------------------------
# HELPERS
# -------------------------
def read(path: Path) -> str:
    return path.read_text(errors="ignore").strip()


def retrieve_context(query: str, k: int = 4) -> str:
    db = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=OllamaEmbeddings(model="nomic-embed-text"),
    )
    docs = db.similarity_search(query, k=k)
    return "\n\n".join(d.page_content for d in docs)


def think(prompt: str) -> str:
    r = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    output = r.stdout.strip() or r.stderr.strip()
    if not output:
        return "[NO OUTPUT FROM MODEL]"

    return output


def build_prompt(context: str, resume: str, job: str, rules: str) -> str:
    return f"""
You are assisting with an ENTRY-LEVEL SOC / Junior Cybersecurity Analyst resume.

STRICT CONSTRAINTS:
- All experience is lab-based, academic, or simulated.
- Do NOT imply production SOC, MSSP, or enterprise responsibility.
- Every bullet must be defensible if an interviewer asks: "How do you know?"
- Avoid buzzwords unless clearly supported by evidence.

OPERATING PRINCIPLES:
- Frame work using SOC workflows: detection, triage, investigation, documentation, escalation.
- Prefer DNS, HTTP, TCP session analysis over payload reverse engineering.
- Describe observations and outcomes, not just tools.

RESUME RULES:
{rules}

REFERENCE CONTEXT:
{context}

CURRENT RESUME:
{resume}

TARGET JOB DESCRIPTION:
{job}

TASKS:
1) Rewrite resume bullets to align with the job description.
2) Translate lab and support work into SOC-style investigative language.
3) Produce 8–12 ATS / SOC-relevant keywords.
4) Briefly explain why the changes improve alignment.

OUTPUT FORMAT (exact):
- Revised Resume Bullets
- ATS / SOC Keywords
- Explanation of Changes
"""


# -------------------------
# MAIN
# -------------------------
def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    resume = read(RESUME)
    job = read(JOB)
    rules = read(RULES)

    context = retrieve_context(
        query="entry-level SOC analyst skills, log analysis, Wireshark, SIEM",
        k=4,
    )

    for i in range(MAX_ITERATIONS):
        prompt = build_prompt(context, resume, job, rules)
        output = think(prompt)

        out = OUTDIR / f"iteration_{i:03d}.txt"
        out.write_text(output)

        print(f"[{i}] wrote {out.name}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()

