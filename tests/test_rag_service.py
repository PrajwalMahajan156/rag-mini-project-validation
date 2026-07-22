"""
Unit tests for RAGService – vector store lifecycle and context retrieval.

FAISS.load_local is patched via its origin module so the patch takes effect
regardless of where the name was imported, avoiding real disk I/O.
"""

from unittest.mock import MagicMock, patch

import pytest

# Patch target for FAISS.load_local – must match where FAISS is defined.
_FAISS_LOAD_LOCAL = "langchain_community.vectorstores.faiss.FAISS.load_local"
_DATA_DIR = "app.core.config.Config.DATA_DIR"


class TestRAGServiceQueryDocument:
    """Tests for RAGService.query_document."""

    def test_query_raises_when_vector_store_missing(self, tmp_path):
        """query_document must raise FileNotFoundError for an unknown document_id."""
        with patch(_DATA_DIR, str(tmp_path)):
            from app.services.rag_service import RAGService

            # tmp_path has no subdirectory for this document_id → should fail
            svc = RAGService.__new__(RAGService)
            # Manually set attributes so __init__ (which calls Gemini) is skipped
            svc.embeddings = MagicMock()
            svc.text_splitter = MagicMock()

            with pytest.raises(FileNotFoundError, match="not found"):
                svc.query_document("test query", "nonexistent-doc-id")

    def test_query_returns_list_of_strings(self, tmp_path):
        """query_document should return the page_content strings from the vector store."""
        store_path = tmp_path / "vector_store_doc123"
        store_path.mkdir()

        mock_doc = MagicMock()
        mock_doc.page_content = "relevant chunk text"
        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [mock_doc, mock_doc]

        with (
            patch(_DATA_DIR, str(tmp_path)),
            patch(_FAISS_LOAD_LOCAL, return_value=mock_vs),
        ):
            from app.services.rag_service import RAGService

            svc = RAGService.__new__(RAGService)
            svc.embeddings = MagicMock()
            svc.text_splitter = MagicMock()

            results = svc.query_document("my query", "doc123", k=2)

        assert isinstance(results, list)
        assert all(isinstance(r, str) for r in results)
        assert results == ["relevant chunk text", "relevant chunk text"]


class TestRAGServiceGetContextText:
    """Tests for RAGService.get_context_text output formatting."""

    def test_context_text_joins_chunks_with_double_newline(self, tmp_path):
        """get_context_text should join retrieved chunks with double newlines."""
        store_path = tmp_path / "vector_store_doc456"
        store_path.mkdir()

        doc_a = MagicMock()
        doc_a.page_content = "chunk A"
        doc_b = MagicMock()
        doc_b.page_content = "chunk B"
        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [doc_a, doc_b]

        with (
            patch(_DATA_DIR, str(tmp_path)),
            patch(_FAISS_LOAD_LOCAL, return_value=mock_vs),
        ):
            from app.services.rag_service import RAGService

            svc = RAGService.__new__(RAGService)
            svc.embeddings = MagicMock()
            svc.text_splitter = MagicMock()

            ctx = svc.get_context_text("query", "doc456")

        assert ctx == "chunk A\n\nchunk B"

    def test_context_text_empty_when_no_chunks(self, tmp_path):
        """get_context_text returns an empty string when no chunks match the query."""
        store_path = tmp_path / "vector_store_empty"
        store_path.mkdir()

        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = []

        with (
            patch(_DATA_DIR, str(tmp_path)),
            patch(_FAISS_LOAD_LOCAL, return_value=mock_vs),
        ):
            from app.services.rag_service import RAGService

            svc = RAGService.__new__(RAGService)
            svc.embeddings = MagicMock()
            svc.text_splitter = MagicMock()

            ctx = svc.get_context_text("query", "empty")

        assert ctx == ""
