"""Knowledge base indexing pipeline for RAG system."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openfatture.ai.rag.config import RAGConfig, get_rag_config
from openfatture.ai.rag.embeddings import create_embeddings
from openfatture.ai.rag.vector_store import VectorStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class KnowledgeSource:
    """Single knowledge source definition loaded from manifest."""

    id: str
    type: str
    path: Path
    description: str | None = None
    enabled: bool = True
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    chunk_max_chars: int = 1800
    chunk_overlap: int = 200


class KnowledgeIndexer:
    """Indexer for static knowledge base documents (Markdown/YAML/Plaintext)."""

    def __init__(
        self,
        config: RAGConfig,
        vector_store: VectorStore,
        manifest_path: Path | None = None,
        base_path: Path | None = None,
    ) -> None:
        self.config = config
        self.vector_store = vector_store
        self.base_path = base_path or Path(".").resolve()
        self.manifest_path = (
            Path(manifest_path) if manifest_path else config.knowledge_manifest_path
        )
        self.sources = self._load_manifest()

        logger.info(
            "knowledge_indexer_initialized",
            collection=self.config.collection_name,
            sources=len(self.sources),
            manifest=str(self.manifest_path),
        )

    @classmethod
    async def create(
        cls,
        config: RAGConfig | None = None,
        api_key: str | None = None,
        manifest_path: Path | None = None,
        base_path: Path | None = None,
    ) -> KnowledgeIndexer:
        """Factory helper to build a KnowledgeIndexer with embeddings."""
        config = config or get_rag_config()
        kb_config = config.model_copy(
            update={
                "collection_name": config.knowledge_collection_name,
            }
        )

        embeddings = create_embeddings(kb_config, api_key=api_key)
        vector_store = VectorStore(kb_config, embeddings)

        return cls(
            config=kb_config,
            vector_store=vector_store,
            manifest_path=manifest_path,
            base_path=base_path,
        )

    def get_source(self, source_id: str) -> KnowledgeSource | None:
        """Return a source definition by id."""
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    async def index_sources(self, source_ids: Iterable[str] | None = None) -> int:
        """
        Index all enabled sources (or selected ones) into the vector store.

        Args:
            source_ids: Optional iterable of source IDs to restrict indexing.

        Returns:
            Total chunks indexed.
        """
        total_chunks = 0

        for source in self.sources:
            if not source.enabled:
                logger.debug("knowledge_source_skipped_disabled", source_id=source.id)
                continue

            if source_ids and source.id not in source_ids:
                continue

            chunks_indexed = await self._index_single_source(source)
            total_chunks += chunks_indexed

        logger.info("knowledge_sources_indexed", total_chunks=total_chunks)
        return total_chunks

    async def index_source(self, source_id: str) -> int:
        """Index a single source by id."""
        source = self.get_source(source_id)
        if source is None:
            raise ValueError(f"Knowledge source '{source_id}' not found")

        if not source.enabled:
            logger.warning("knowledge_source_disabled", source_id=source_id)
            return 0

        return await self._index_single_source(source)

    async def _index_single_source(self, source: KnowledgeSource) -> int:
        """Index one source definition."""
        absolute_path = (
            source.path if source.path.is_absolute() else (self.base_path / source.path).resolve()
        )
        if not absolute_path.exists():
            logger.warning(
                "knowledge_source_missing",
                source_id=source.id,
                path=str(absolute_path),
            )
            return 0

        raw_text = absolute_path.read_text(encoding="utf-8")

        if source.type.lower() == "markdown":
            sections = self._parse_markdown(raw_text)
        else:
            sections = [{"title": source.id, "content": raw_text}]

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        chunk_counter = 0

        for section in sections:
            section_title = section["title"]
            section_chunks = self._chunk_text(
                section["content"],
                max_chars=source.chunk_max_chars,
                overlap=source.chunk_overlap,
            )

            for index, chunk in enumerate(section_chunks):
                chunk_counter += 1
                documents.append(chunk)
                metadata = {
                    "type": "knowledge",
                    "knowledge_source": source.id,
                    "section_title": section_title,
                    "chunk_index": index,
                    "total_chunks": len(section_chunks),
                    "tags": source.tags or [],
                    "source_path": str(source.path),
                }

                if source.metadata:
                    metadata.update(source.metadata)

                metadatas.append(metadata)
                ids.append(self._build_document_id(source.id, section_title, index))

        if not documents:
            logger.info("knowledge_source_empty", source_id=source.id)
            return 0

        await self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(
            "knowledge_source_indexed",
            source_id=source.id,
            path=str(source.path),
            chunks=len(documents),
        )

        return len(documents)

    def _load_manifest(self) -> list[KnowledgeSource]:
        """Load manifest JSON file and build KnowledgeSource objects."""
        manifest_file = (
            self.manifest_path
            if self.manifest_path.is_absolute()
            else (self.base_path / self.manifest_path).resolve()
        )

        if not manifest_file.exists():
            raise FileNotFoundError(f"Knowledge base manifest not found at {manifest_file}")

        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        sources_data = data.get("sources", [])

        sources: list[KnowledgeSource] = []
        for entry in sources_data:
            chunking = entry.get("chunking", {})
            source = KnowledgeSource(
                id=entry["id"],
                type=entry.get("type", "markdown"),
                path=Path(entry["path"]),
                description=entry.get("description"),
                enabled=entry.get("enabled", True),
                tags=entry.get("tags", []),
                metadata=entry.get("metadata", {}),
                chunk_max_chars=chunking.get("max_chars", 1800),
                chunk_overlap=chunking.get("overlap", 200),
            )
            sources.append(source)

        return sources

    @staticmethod
    def _parse_markdown(text: str) -> list[dict[str, str]]:
        """
        Very lightweight markdown section parser (split by headings).

        Args:
            text: markdown content

        Returns:
            List of {"title": str, "content": str}
        """
        sections: list[dict[str, str]] = []
        current_title = "Introduzione"
        current_lines: list[str] = []

        heading_pattern = re.compile(r"^(#{1,6})\s+(.*)")

        for line in text.splitlines():
            match = heading_pattern.match(line)
            if match:
                if current_lines:
                    sections.append(
                        {"title": current_title, "content": "\n".join(current_lines).strip()}
                    )
                current_title = match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({"title": current_title, "content": "\n".join(current_lines).strip()})

        return sections

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 1800, overlap: int = 200) -> list[str]:
        """Simple character-based chunking with overlap."""
        if not text:
            return []

        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            end = min(start + max_chars, text_length)
            chunks.append(normalized[start:end])
            if end == text_length:
                break
            start = max(0, end - overlap)

        return chunks

    @staticmethod
    def _build_document_id(source_id: str, title: str, chunk_index: int) -> str:
        """Create deterministic document ids."""
        slug = KnowledgeIndexer._slugify(title) or "section"
        return f"kb-{source_id}-{slug}-{chunk_index}"

    @staticmethod
    def _slugify(value: str) -> str:
        """Generate URL-safe slug from value."""
        value = value.lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-{2,}", "-", value)
        return value.strip("-")
