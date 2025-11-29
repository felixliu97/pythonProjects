"""Local Retrieval-Augmented Generation helper that runs fully offline once
the Ollama models are cached locally.

The script:
1. Verifies a knowledge base folder exists (prompting the user if empty).
2. Ensures Ollama is reachable and lists installed models.
3. Picks sensible defaults for LLM + embedding models based on what is
   available locally (or uses the CLI overrides).
4. Builds/loads a LlamaIndex vector store and exposes a lightweight chat loop.
"""

from __future__ import annotations
import sys
import argparse
import subprocess
import requests
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.node_parser import SentenceSplitter


def ensure_data_dir(data_folder: Path) -> None:
    """Ensure the knowledge base folder exists before continuing."""

    if data_folder.exists():
        return
    print(f"Creating data directory: {data_folder}")
    data_folder.mkdir(parents=True, exist_ok=True)
    print(f"Add your PDF/TXT documents to {data_folder} and restart.")
    sys.exit(0)


def check_ollama() -> None:
    """Confirm the Ollama HTTP API is responding on the default port."""

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("Error: Ollama is not responding correctly.")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("Error: Could not connect to Ollama.")
        print("Ensure Ollama is running (e.g., 'ollama serve').")
        sys.exit(1)


def list_installed_models() -> list[str]:
    """Return every installed Ollama model name via `ollama list`."""

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: unable to run 'ollama list'. Is Ollama installed and running?")
        sys.exit(1)

    models = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line or line.lower().startswith("name"):
            continue
        models.append(line.split()[0])
    return models


def resolve_model(requested: str | None, candidates: list[str], role: str, hint: str) -> str:
    """Choose a model for the given role, preferring CLI overrides."""

    if requested:
        if requested in candidates:
            return requested
        print(f"Error: requested {role} model '{requested}' is not installed.")
        print(f"Install it with: ollama pull {requested}")
        sys.exit(1)

    if candidates:
        choice = candidates[0]
        print(f"Using installed {role} model '{choice}'.")
        return choice

    print(f"No installed {role} models found. {hint}")
    sys.exit(1)


def configure_llama_index(llm_model: str, embed_model: str) -> None:
    """Wire the selected Ollama models into the global LlamaIndex settings."""

    Settings.llm = Ollama(model=llm_model, request_timeout=360.0, temperature=0)
    Settings.embed_model = OllamaEmbedding(model_name=embed_model)


def load_or_create_index(
    data_folder: Path,
    db_folder: Path,
    chunk_size: int = 350,
    chunk_overlap: int = 50,
) -> VectorStoreIndex:
    """Load an existing persisted index or build one from the document folder."""

    docstore_file = db_folder / "docstore.json"
    if docstore_file.exists():
        print("Loading existing knowledge base...")
        storage_context = StorageContext.from_defaults(persist_dir=str(db_folder))
        return load_index_from_storage(storage_context)

    print("First time setup: indexing your documents...")
    documents = SimpleDirectoryReader(str(data_folder), recursive=True).load_data()
    if not documents:
        print(f"No documents found in {data_folder}. Add files and try again.")
        sys.exit(0)

    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    db_folder.mkdir(parents=True, exist_ok=True)
    storage_context = StorageContext.from_defaults()
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[splitter],
        show_progress=True,
    )
    index.storage_context.persist(persist_dir=str(db_folder))
    print(f"Indexed {len(documents)} documents → saved to {db_folder}")
    return index


def create_query_engine(index: VectorStoreIndex, top_k: int = 3, streaming: bool = False):
    """Build a tuned query engine with conservative defaults for speed."""

    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        response_mode="compact",
        streaming=streaming,
    )
    query_engine.update_prompts({
        "response_synthesizer:text_qa":
            "You are an accurate assistant. "
            "Answer using ONLY the retrieved context below. "
            "If the context does not contain the answer, say "
            "'I do not have that information in my local knowledge base.' "
            "Always cite the source file names. Never make up facts.\n\n"
            "Context:\n{context_str}\n\nQuestion: {query_str}"
    })
    return query_engine


def chat_loop(query_engine, llm_model: str) -> None:
    """Run an interactive prompt/response loop against the query engine."""

    print(f"\nLocal RAG ready with {llm_model}! Ask questions (type 'quit' to exit)\n")
    while True:
        try:
            question = input("You: ")
            if question.lower() in {"quit", "exit"}:
                break
            if not question.strip():
                continue

            response = query_engine.query(question)
            print("\nAnswer:", end=" ", flush=True)
            if hasattr(response, "response_gen") and response.response_gen:
                for token in response.response_gen:
                    print(token, end="", flush=True)
                print()
            else:
                print(response.response if hasattr(response, "response") else str(response))
            print()

            print("Sources:")
            for node in response.source_nodes:
                source = node.node.metadata.get("file_name", "unknown")
                print(f"  • {source} (score: {node.score:.3f})")
            print("\n" + "-" * 80)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as exc:
            print(f"An error occurred: {exc}")


def parse_args():
    """Parse CLI flags; defaults favor automatic model selection."""

    parser = argparse.ArgumentParser(description="Local RAG with Ollama")
    parser.add_argument("--llm-model", help="Ollama LLM model to use")
    parser.add_argument("--embed-model", help="Embedding model to use")
    parser.add_argument("--data-dir", default="knowledge_base", help="Directory containing documents")
    parser.add_argument("--db-dir", default="local_chroma_db", help="Directory for vector database")
    return parser.parse_args()


def main():
    """Bootstrap the local RAG pipeline end-to-end."""

    args = parse_args()
    base_dir = Path(__file__).resolve().parent
    data_folder = base_dir / args.data_dir
    db_folder = base_dir / args.db_dir

    ensure_data_dir(data_folder)
    check_ollama()
    installed = list_installed_models()
    if not installed:
        print("No Ollama models installed. Install one with 'ollama pull <model>'.")
        sys.exit(1)

    # Crude heuristic: treat models containing "embed" as embedding models.
    embed_candidates = [m for m in installed if "embed" in m.lower()]
    llm_candidates = [m for m in installed if m not in embed_candidates]

    llm_model = resolve_model(
        args.llm_model,
        llm_candidates or installed,
        "LLM",
        "Install one with: ollama pull llama3.2:3b (or similar).",
    )
    embed_model = resolve_model(
        args.embed_model,
        embed_candidates,
        "embedding",
        "Install one with: ollama pull nomic-embed-text.",
    )

    configure_llama_index(llm_model, embed_model)
    index = load_or_create_index(data_folder, db_folder)
    query_engine = create_query_engine(index)
    chat_loop(query_engine, llm_model)


if __name__ == "__main__":
    main()