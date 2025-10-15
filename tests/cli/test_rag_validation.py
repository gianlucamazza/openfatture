"""
Validation tests for RAG (Retrieval-Augmented Generation) CLI commands.
Tests edge cases and validation for knowledge base management commands.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.ai import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestRAGStatusCommandValidation:
    """Test validation for 'ai rag status' command."""

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_status_success(self, mock_create_indexer):
        """Test RAG status command with successful indexer creation."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_vector_store = Mock()
        mock_vector_store.get_stats.return_value = {
            "collection_name": "test_collection",
            "document_count": 10,
            "persist_directory": "/tmp/test",
        }
        mock_indexer.vector_store = mock_vector_store

        # Mock sources
        mock_source = Mock()
        mock_source.id = "docs"
        mock_source.enabled = True
        mock_source.path = "/path/to/docs"
        mock_source.tags = ["help", "docs"]
        mock_indexer.sources = [mock_source]

        # Mock the async function to return a coroutine that resolves to mock_indexer
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "status"])

        assert result.exit_code == 0
        assert "Knowledge Base Sources" in result.stdout
        assert "Vector Store" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_status_error(self, mock_create_indexer):
        """Test RAG status command with indexer creation error."""
        mock_create_indexer.side_effect = RuntimeError("Indexer creation failed")

        result = runner.invoke(app, ["rag", "status"])

        assert result.exit_code == 0  # Command should handle errors gracefully
        assert "Errore:" in result.stdout


class TestRAGIndexCommandValidation:
    """Test validation for 'ai rag index' command."""

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_index_success(self, mock_create_indexer):
        """Test RAG index command with successful indexing."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.index_sources.return_value = 5  # 5 chunks indexed
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "index"])

        assert result.exit_code == 0
        assert "Indicizzazione completata" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_index_with_sources(self, mock_create_indexer):
        """Test RAG index command with specific sources."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.index_sources.return_value = 3
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "index", "--source", "docs", "--source", "faq"])

        assert result.exit_code == 0
        assert "Indicizzazione completata" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_index_error(self, mock_create_indexer):
        """Test RAG index command with indexer creation error."""
        mock_create_indexer.side_effect = RuntimeError("Indexer creation failed")

        result = runner.invoke(app, ["rag", "index"])

        assert result.exit_code == 0  # Command should handle errors gracefully
        assert "Errore:" in result.stdout


class TestRAGSearchCommandValidation:
    """Test validation for 'ai rag search' command."""

    def test_rag_search_required_query(self):
        """Test that search query is required."""
        result = runner.invoke(app, ["rag", "search"])

        # Should show error about missing argument
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "requires an argument" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_search_success(self, mock_create_indexer):
        """Test RAG search command with successful search."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.vector_store.search.return_value = [
            {
                "document": "This is a test document about invoices",
                "similarity": 0.85,
                "metadata": {"knowledge_source": "docs", "section_title": "Invoice Creation"},
            }
        ]
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "search", "how to create invoice"])

        assert result.exit_code == 0
        assert "Risultati per" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_search_with_source_filter(self, mock_create_indexer):
        """Test RAG search command with source filter."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.vector_store.search.return_value = []
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "search", "invoice", "--source", "docs"])

        assert result.exit_code == 0
        # Search should execute without error even if no results

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_search_with_top_k(self, mock_create_indexer):
        """Test RAG search command with top-k parameter."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.vector_store.search.return_value = []
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "search", "invoice", "--top", "3"])

        assert result.exit_code == 0
        # Search should execute without error

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_search_empty_results(self, mock_create_indexer):
        """Test RAG search command with no results."""
        # Mock indexer
        mock_indexer = AsyncMock()
        mock_indexer.vector_store.search.return_value = []
        mock_create_indexer.return_value = mock_indexer

        result = runner.invoke(app, ["rag", "search", "nonexistent term"])

        assert result.exit_code == 0
        assert "Nessun risultato trovato" in result.stdout

    @patch("openfatture.cli.commands.ai._create_knowledge_indexer")
    def test_rag_search_error(self, mock_create_indexer):
        """Test RAG search command with indexer creation error."""
        mock_create_indexer.side_effect = RuntimeError("Indexer creation failed")

        result = runner.invoke(app, ["rag", "search", "invoice"])

        assert result.exit_code == 0  # Command should handle errors gracefully
        assert "Errore:" in result.stdout
