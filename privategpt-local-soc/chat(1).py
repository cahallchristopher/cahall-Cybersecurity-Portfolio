"""
chat.py — Command-line chat interface for PrivateGPT Local.

Usage:
  python chat.py

Commands inside chat:
  /quit or /exit  — Exit
  /clear          — Clear conversation history
  /sources        — Show what's been ingested
"""

import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def get_retriever():
    """Build the ChromaDB retriever."""
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions as ef
    from config import CHROMA_DIR, CHROMA_COLLECTION, OLLAMA_BASE_URL, EMBED_MODEL, NUM_CHUNKS

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection(CHROMA_COLLECTION)
    except Exception:
        console.print("[red]No documents found. Run ingest.py first.[/red]")
        sys.exit(1)

    count = collection.count()
    if count == 0:
        console.print("[red]Vector store is empty. Run ingest.py first.[/red]")
        sys.exit(1)

    console.print(f"[dim]Loaded vector store with {count} chunks.[/dim]")

    embedder = ef.OllamaEmbeddingFunction(
        url=f"{OLLAMA_BASE_URL}/api/embeddings",
        model_name=EMBED_MODEL,
    )

    return collection, embedder, NUM_CHUNKS


def retrieve(query: str, collection, embedder, n_results: int) -> list[dict]:
    """Find the most relevant chunks for a query."""
    query_embedding = embedder([query])
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "source": meta.get("source", "?"), "distance": dist})

    return chunks


def build_prompt(query: str, chunks: list[dict], history: list[dict]) -> list[dict]:
    """Build the full message list for Ollama."""
    from config import SYSTEM_PROMPT

    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f"[Source {i}: {c['source']}]\n{c['text']}")
    context = "\n\n---\n\n".join(context_parts)

    system = f"{SYSTEM_PROMPT}\n\nContext from documents:\n\n{context}"

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    return messages


def ask_ollama(messages: list[dict]) -> str:
    """Send messages to Ollama and return the response."""
    import requests
    from config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
        }
    }

    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def show_sources(chunks: list[dict]):
    """Print the source chunks used for the answer."""
    console.print("\n[dim]Sources used:[/dim]")
    seen = set()
    for c in chunks:
        if c["source"] not in seen:
            console.print(f"  [dim cyan]• {c['source']}[/dim cyan]")
            seen.add(c["source"])


def main():
    from config import LLM_MODEL, UI_TITLE

    console.print(Panel(
        f"[bold]{UI_TITLE}[/bold]\n"
        f"Model: [cyan]{LLM_MODEL}[/cyan]\n"
        "Type [bold]/quit[/bold] to exit, [bold]/clear[/bold] to reset, [bold]/sources[/bold] to list docs",
        title="PrivateGPT Local CLI",
        border_style="green",
    ))

    # Check Ollama is running
    try:
        import requests
        from config import OLLAMA_BASE_URL
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    except Exception:
        console.print("[red]Cannot reach Ollama. Make sure it's running: `ollama serve`[/red]")
        sys.exit(1)

    collection, embedder, n_results = get_retriever()
    history = []

    while True:
        try:
            query = Prompt.ask("\n[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not query.strip():
            continue

        # Commands
        if query.strip().lower() in ("/quit", "/exit"):
            console.print("[dim]Goodbye![/dim]")
            break
        elif query.strip().lower() == "/clear":
            history = []
            console.print("[dim]Conversation cleared.[/dim]")
            continue
        elif query.strip().lower() == "/sources":
            from ingest import list_sources
            list_sources()
            continue

        # Retrieve + generate
        try:
            with console.status("[dim]Searching documents...[/dim]"):
                chunks = retrieve(query, collection, embedder, n_results)

            messages = build_prompt(query, chunks, history)

            with console.status("[dim]Thinking...[/dim]"):
                answer = ask_ollama(messages)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            continue

        # Show answer
        console.print("\n[bold blue]Assistant[/bold blue]")
        console.print(Markdown(answer))
        show_sources(chunks)

        # Update history (keep last 10 turns)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 20:
            history = history[-20:]


if __name__ == "__main__":
    main()
