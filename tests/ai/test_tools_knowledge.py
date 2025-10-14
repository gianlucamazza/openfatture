"""Tests for knowledge tools.

Tests focus on individual tool functions in isolation using mocks
to avoid external dependencies on RAG and vector stores.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.tools.knowledge_tools import (
    get_knowledge_tools,
    search_knowledge_base,
)


class TestSearchKnowledgeBase:
    """Test search_knowledge_base tool function."""

    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_rag_disabled(self, mock_getenv, mock_get_rag_config):
        """Test knowledge search when RAG is disabled."""
        # Mock RAG config as disabled
        mock_config = MagicMock()
        mock_config.enabled = False
        mock_get_rag_config.return_value = mock_config

        result = await search_knowledge_base("test query")

        assert result["results"] == []
        assert result["count"] == 0
        assert result["message"] == "RAG disabled"

    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_missing_api_key(self, mock_getenv, mock_get_rag_config):
        """Test knowledge search when OpenAI API key is missing."""
        # Mock RAG config as enabled with OpenAI provider
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "openai"
        mock_get_rag_config.return_value = mock_config

        # Mock missing API key
        mock_getenv.return_value = None

        result = await search_knowledge_base("test query")

        assert result["results"] == []
        assert result["count"] == 0
        assert "error" in result
        assert "OPENAI_API_KEY non impostata" in result["error"]

    @patch("openfatture.ai.tools.knowledge_tools.KnowledgeIndexer")
    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_success(
        self, mock_getenv, mock_get_rag_config, mock_knowledge_indexer
    ):
        """Test successful knowledge base search."""
        # Mock RAG config
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "ollama"  # No API key needed
        mock_get_rag_config.return_value = mock_config

        # Mock API key (not needed for ollama)
        mock_getenv.return_value = "fake-key"

        # Mock KnowledgeIndexer.create to return a coroutine
        mock_indexer_instance = AsyncMock()

        async def mock_create(*args, **kwargs):
            return mock_indexer_instance

        mock_knowledge_indexer.create = mock_create

        # Mock search results
        mock_results = [
            {
                "document": "This is a test document about reverse charge in construction.",
                "metadata": {
                    "knowledge_source": "tax_guides",
                    "section_title": "Reverse Charge Edilizia",
                    "law_reference": "Art. 17-bis DPR 633/72",
                    "source_path": "/docs/tax_guides/reverse_charge.pdf",
                },
                "similarity": 0.85,
            },
            {
                "document": "Another document about VAT regulations.",
                "metadata": {
                    "knowledge_source": "vat_manual",
                    "section_title": "IVA Ordinaria",
                    "source_path": "/docs/vat_manual.pdf",
                },
                "similarity": 0.72,
            },
        ]
        mock_indexer_instance.vector_store.search.return_value = mock_results

        result = await search_knowledge_base("reverse charge edilizia")

        assert result["count"] == 2
        assert len(result["results"]) == 2

        # Check first result
        first_result = result["results"][0]
        assert first_result["source"] == "tax_guides"
        assert first_result["section"] == "Reverse Charge Edilizia"
        assert first_result["citation"] == "Art. 17-bis DPR 633/72"
        assert first_result["source_path"] == "/docs/tax_guides/reverse_charge.pdf"
        assert first_result["similarity"] == 0.85
        assert "reverse charge" in first_result["excerpt"].lower()

        # Check second result
        second_result = result["results"][1]
        assert second_result["source"] == "vat_manual"
        assert second_result["section"] == "IVA Ordinaria"
        assert (
            second_result["citation"] == "IVA Ordinaria"
        )  # Fallback to section_title when no law_reference
        assert second_result["similarity"] == 0.72

    @patch("openfatture.ai.tools.knowledge_tools.KnowledgeIndexer")
    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_with_source_filter(
        self, mock_getenv, mock_get_rag_config, mock_knowledge_indexer
    ):
        """Test knowledge search with source filter."""
        # Mock RAG config
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "ollama"
        mock_get_rag_config.return_value = mock_config

        mock_getenv.return_value = "fake-key"

        # Mock KnowledgeIndexer.create to return a coroutine
        mock_indexer_instance = AsyncMock()

        async def mock_create(*args, **kwargs):
            return mock_indexer_instance

        mock_knowledge_indexer.create = mock_create

        mock_results = [
            {
                "document": "Filtered result from specific source.",
                "metadata": {
                    "knowledge_source": "tax_guides",
                    "section_title": "Test Section",
                },
                "similarity": 0.9,
            }
        ]
        mock_indexer_instance.vector_store.search.return_value = mock_results

        result = await search_knowledge_base("test query", source="tax_guides", top_k=10)

        assert result["count"] == 1
        assert result["results"][0]["source"] == "tax_guides"

        # Verify that search was called with correct filters
        mock_indexer_instance.vector_store.search.assert_called_once()
        call_args = mock_indexer_instance.vector_store.search.call_args
        assert call_args[1]["query"] == "test query"
        assert call_args[1]["top_k"] == 10
        assert call_args[1]["filters"] == {"type": "knowledge", "knowledge_source": "tax_guides"}

    @patch("openfatture.ai.tools.knowledge_tools.KnowledgeIndexer")
    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_empty_results(
        self, mock_getenv, mock_get_rag_config, mock_knowledge_indexer
    ):
        """Test knowledge search with no results."""
        # Mock RAG config
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "ollama"
        mock_get_rag_config.return_value = mock_config

        mock_getenv.return_value = "fake-key"

        # Mock KnowledgeIndexer.create to return a coroutine
        mock_indexer_instance = AsyncMock()

        async def mock_create(*args, **kwargs):
            return mock_indexer_instance

        mock_knowledge_indexer.create = mock_create

        # Mock empty results
        mock_indexer_instance.vector_store.search.return_value = []

        result = await search_knowledge_base("nonexistent topic")

        assert result["count"] == 0
        assert result["results"] == []

    @patch("openfatture.ai.tools.knowledge_tools.KnowledgeIndexer")
    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_long_excerpt(
        self, mock_getenv, mock_get_rag_config, mock_knowledge_indexer
    ):
        """Test knowledge search with long document excerpts."""
        # Mock RAG config
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "ollama"
        mock_get_rag_config.return_value = mock_config

        mock_getenv.return_value = "fake-key"

        # Mock KnowledgeIndexer.create to return a coroutine
        mock_indexer_instance = AsyncMock()

        async def mock_create(*args, **kwargs):
            return mock_indexer_instance

        mock_knowledge_indexer.create = mock_create

        # Mock result with very long document
        long_document = "A" * 500  # 500 character document
        mock_results = [
            {
                "document": long_document,
                "metadata": {
                    "knowledge_source": "test",
                    "section_title": "Long Document",
                },
                "similarity": 0.8,
            }
        ]
        mock_indexer_instance.vector_store.search.return_value = mock_results

        result = await search_knowledge_base("test query")

        assert result["count"] == 1
        excerpt = result["results"][0]["excerpt"]
        assert len(excerpt) == 401  # 400 chars + "…"
        assert excerpt.endswith("…")

    @patch("openfatture.ai.tools.knowledge_tools.KnowledgeIndexer")
    @patch("openfatture.ai.tools.knowledge_tools.get_rag_config")
    @patch("openfatture.ai.tools.knowledge_tools.os.getenv")
    @pytest.mark.asyncio
    async def test_search_knowledge_base_missing_metadata(
        self, mock_getenv, mock_get_rag_config, mock_knowledge_indexer
    ):
        """Test knowledge search with incomplete metadata."""
        # Mock RAG config
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.embedding_provider = "ollama"
        mock_get_rag_config.return_value = mock_config

        mock_getenv.return_value = "fake-key"

        # Mock KnowledgeIndexer.create to return a coroutine
        mock_indexer_instance = AsyncMock()

        async def mock_create(*args, **kwargs):
            return mock_indexer_instance

        mock_knowledge_indexer.create = mock_create

        # Mock result with minimal metadata
        mock_results = [
            {
                "document": "Test document",
                "metadata": {},  # Empty metadata
                "similarity": 0.75,
            }
        ]
        mock_indexer_instance.vector_store.search.return_value = mock_results

        result = await search_knowledge_base("test query")

        assert result["count"] == 1
        item = result["results"][0]
        assert item["source"] is None
        assert item["section"] is None
        assert item["citation"] is None  # Should fallback to source, but source is None
        assert item["source_path"] is None
        assert item["similarity"] == 0.75
        assert item["excerpt"] == "Test document"


class TestGetKnowledgeTools:
    """Test get_knowledge_tools function."""

    def test_get_knowledge_tools_structure(self):
        """Test that get_knowledge_tools returns properly structured tools."""
        tools = get_knowledge_tools()

        assert len(tools) == 1
        tool = tools[0]

        assert tool.name == "search_knowledge_base"
        assert tool.category == "knowledge"
        assert callable(tool.func)
        assert tool.func == search_knowledge_base

        # Check parameters
        assert len(tool.parameters) == 3

        # Query parameter
        query_param = tool.parameters[0]
        assert query_param.name == "query"
        assert query_param.type.value == "string"
        assert query_param.required is True

        # Source parameter
        source_param = tool.parameters[1]
        assert source_param.name == "source"
        assert source_param.type.value == "string"
        assert source_param.required is False

        # Top-k parameter
        top_k_param = tool.parameters[2]
        assert top_k_param.name == "top_k"
        assert top_k_param.type.value == "integer"
        assert top_k_param.required is False
        assert top_k_param.default == 5

        # Check examples
        assert len(tool.examples) == 2
        assert "search_knowledge_base(query='reverse charge edilizia')" in tool.examples
        assert (
            "search_knowledge_base(query='split payment PA', source='tax_guides')" in tool.examples
        )
