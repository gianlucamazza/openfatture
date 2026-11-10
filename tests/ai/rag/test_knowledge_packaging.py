"""The packaged knowledge base works from any directory and is indexed on first use."""

from pathlib import Path
from typing import Any

import pytest

from openfatture.ai.rag.config import DEFAULT_KNOWLEDGE_MANIFEST, RAGConfig
from openfatture.ai.rag.knowledge_indexer import KnowledgeIndexer


class FakeStore:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def count(self) -> int:
        return len(self.documents)

    async def add_documents(self, documents, metadatas=None, ids=None, **kwargs) -> None:
        for index, document in enumerate(documents):
            self.documents.append(
                {"document": document, "metadata": (metadatas or [{}] * len(documents))[index]}
            )

    async def search(self, query: str, top_k: int = 5, filters=None) -> list[dict[str, Any]]:
        hits = [d for d in self.documents if query.lower() in d["document"].lower()]
        return [{**hit, "similarity": 1.0} for hit in hits[:top_k]]


def test_manifest_and_sources_are_packaged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    indexer = KnowledgeIndexer(RAGConfig(persist_directory=tmp_path / "kb"), FakeStore())

    assert indexer.manifest_path == DEFAULT_KNOWLEDGE_MANIFEST.resolve()
    sources = [s for s in indexer.sources if s.enabled]
    assert sources
    for source in sources:
        assert (indexer.base_path / source.path).is_file(), source.path


@pytest.mark.asyncio
async def test_search_indexes_knowledge_on_first_use(tmp_path, monkeypatch):
    from openfatture.ai.tools import knowledge_tools

    monkeypatch.chdir(tmp_path)
    store = FakeStore()
    config = RAGConfig(
        persist_directory=tmp_path / "kb", embedding_provider="sentence-transformers"
    )

    async def create(**kwargs) -> KnowledgeIndexer:
        return KnowledgeIndexer(config, store)

    monkeypatch.setattr(knowledge_tools, "get_rag_config", lambda: config)
    monkeypatch.setattr(knowledge_tools.KnowledgeIndexer, "create", staticmethod(create))

    result = await knowledge_tools.search_knowledge_base("N2.2")

    assert store.count() > 0
    assert result["count"] >= 1
    assert any("N2.2" in item["excerpt"] for item in result["results"])


def test_default_persist_directory_is_in_data_dir():
    from openfatture.platform.config import get_settings

    assert RAGConfig().persist_directory == Path(get_settings().vector_store_path).resolve()
