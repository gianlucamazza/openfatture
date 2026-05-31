#!/usr/bin/env python3
"""Script per inizializzare il vector store con fatture e knowledge base."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Initialize database BEFORE importing anything that might use SessionLocal
from openfatture.storage.database.base import init_db

init_db()

# Now safe to import modules that use database
from openfatture.ai.rag.config import get_rag_config
from openfatture.ai.rag.embeddings import create_embeddings
from openfatture.ai.rag.indexing import InvoiceIndexer
from openfatture.ai.rag.knowledge_indexer import KnowledgeIndexer
from openfatture.ai.rag.vector_store import VectorStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


async def main() -> None:
    """Main initialization function."""
    print("\n" + "=" * 80)
    print("INIZIALIZZAZIONE VECTOR STORE RAG")
    print("=" * 80)
    print("\n1Database già inizializzato ")

    # Get RAG config
    config = get_rag_config()
    print("\n2Configurazione RAG:")
    print(f"   • Provider: {config.embedding_provider}")
    print(f"   • Model: {config.embedding_model}")
    print(f"   • Collection: {config.collection_name}")
    print(f"   • Knowledge Collection: {config.knowledge_collection_name}")
    print(f"   • Persist Directory: {config.persist_directory}")

    # Create embeddings strategy (requires API key for OpenAI)
    print("\n3Creazione embedding strategy...")
    try:
        # Get API key from environment
        api_key = None
        if config.embedding_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENFATTURE_AI_OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY non trovato. Verifica che sia configurato nel .env"
                )

        embeddings = create_embeddings(config, api_key=api_key)
        print(f" Embedding strategy creata ({config.embedding_provider})")
    except Exception as e:
        print(f" Errore creazione embeddings: {e}")
        print("\nSuggerimento: Verifica che OPENAI_API_KEY sia configurato nel .env")
        sys.exit(1)

    # Initialize vector stores
    print("\n4Inizializzazione vector stores...")

    # Invoice vector store
    invoice_vector_store = VectorStore(config, embeddings)
    print(f" Invoice vector store: {invoice_vector_store.count()} documenti")

    # Knowledge base vector store
    kb_config = config.model_copy(update={"collection_name": config.knowledge_collection_name})
    kb_vector_store = VectorStore(kb_config, embeddings)
    print(f" Knowledge vector store: {kb_vector_store.count()} documenti")

    # Index invoices
    print("\n5Indicizzazione fatture...")
    invoice_indexer = InvoiceIndexer(invoice_vector_store)
    try:
        invoice_count = await invoice_indexer.index_all_invoices(batch_size=100)
        print(f" Fatture indicizzate: {invoice_count}")
        print(f" Totale documenti invoice collection: {invoice_vector_store.count()}")
    except Exception as e:
        print(f" Errore indicizzazione fatture: {e}")
        # Continue with knowledge base even if invoices fail

    # Index knowledge base
    print("\n6Indicizzazione knowledge base...")
    kb_indexer = KnowledgeIndexer(
        config=kb_config,
        vector_store=kb_vector_store,
        base_path=Path(".").resolve(),
    )

    print(" Knowledge sources disponibili:")
    for source in kb_indexer.sources:
        status = "enabled" if source.enabled else "disabled"
        print(f"      • {source.id}: {source.description} ({status})")

    try:
        kb_count = await kb_indexer.index_sources()
        print(f"\n Knowledge base indicizzata: {kb_count} chunks")
        print(f" Totale documenti KB collection: {kb_vector_store.count()}")
    except Exception as e:
        print(f" Errore indicizzazione knowledge base: {e}")

    # Final stats
    print("\n" + "=" * 80)
    print("RIEPILOGO FINALE")
    print("=" * 80)
    print(f"\nInvoice Collection ({config.collection_name}):")
    invoice_stats = invoice_vector_store.get_stats()
    for key, value in invoice_stats.items():
        print(f"   • {key}: {value}")

    print(f"\nKnowledge Base Collection ({config.knowledge_collection_name}):")
    kb_stats = kb_vector_store.get_stats()
    for key, value in kb_stats.items():
        print(f"   • {key}: {value}")

    print("\n" + "=" * 80)
    print("VECTOR STORE INIZIALIZZATO CON SUCCESSO!")
    print("=" * 80)
    print("\nOra puoi testare il RAG con:")
    print("   uv run openfatture ai chat")
    print("   > dimmi le ultime fatture emesse\n")


if __name__ == "__main__":
    asyncio.run(main())
