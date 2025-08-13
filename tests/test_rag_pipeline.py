import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from rag.rag_pipeline import RAGPipeline, RAGResult, DocumentChunk
from rag.vector_store import VectorStore
from rag.embedding_client import EmbeddingClient
from rag.document_processor import DocumentProcessor


class TestRAGPipeline:
    """Test cases for RAGPipeline class"""
    
    @pytest.fixture
    def mock_embedding_client(self):
        """Mock embedding client"""
        client = Mock(spec=EmbeddingClient)
        client.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        client.embed_batch.return_value = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.6, 0.7, 0.8, 0.9, 1.0]
        ]
        return client
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store"""
        store = Mock(spec=VectorStore)
        store.add_document.return_value = "doc_123"
        store.search.return_value = [
            DocumentChunk(
                id="chunk_1",
                content="This is a test document chunk about diabetes management.",
                metadata={"source": "diabetes_guide.md", "chunk_index": 0},
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
            ),
            DocumentChunk(
                id="chunk_2", 
                content="Another chunk about blood sugar monitoring.",
                metadata={"source": "diabetes_guide.md", "chunk_index": 1},
                embedding=[0.6, 0.7, 0.8, 0.9, 1.0]
            )
        ]
        return store
    
    @pytest.fixture
    def mock_document_processor(self):
        """Mock document processor"""
        processor = Mock(spec=DocumentProcessor)
        processor.process_document.return_value = [
            DocumentChunk(
                id="chunk_1",
                content="Test content 1",
                metadata={"source": "test.md", "chunk_index": 0},
                embedding=None
            ),
            DocumentChunk(
                id="chunk_2",
                content="Test content 2", 
                metadata={"source": "test.md", "chunk_index": 1},
                embedding=None
            )
        ]
        return processor
    
    @pytest.fixture
    def rag_pipeline(self, mock_embedding_client, mock_vector_store, mock_document_processor):
        """RAG pipeline instance with mocked dependencies"""
        return RAGPipeline(
            embedding_client=mock_embedding_client,
            vector_store=mock_vector_store,
            document_processor=mock_document_processor
        )
    
    def test_rag_pipeline_initialization(self, rag_pipeline):
        """Test RAG pipeline initialization"""
        assert rag_pipeline.embedding_client is not None
        assert rag_pipeline.vector_store is not None
        assert rag_pipeline.document_processor is not None
    
    def test_query_pipeline_success(self, rag_pipeline, mock_vector_store):
        """Test successful query processing"""
        query = "How to manage diabetes?"
        result = rag_pipeline.query(query, top_k=2)
        
        assert isinstance(result, RAGResult)
        assert result.query == query
        assert len(result.documents) == 2
        assert result.documents[0].content == "This is a test document chunk about diabetes management."
        assert result.documents[1].content == "Another chunk about blood sugar monitoring."
        
        # Verify vector store search was called
        mock_vector_store.search.assert_called_once()
    
    def test_query_pipeline_no_results(self, rag_pipeline, mock_vector_store):
        """Test query with no results"""
        mock_vector_store.search.return_value = []
        
        query = "Non-existent topic"
        result = rag_pipeline.query(query, top_k=2)
        
        assert isinstance(result, RAGResult)
        assert result.query == query
        assert len(result.documents) == 0
        assert result.context == ""
    
    def test_add_document_success(self, rag_pipeline, mock_document_processor, mock_embedding_client, mock_vector_store):
        """Test successful document addition"""
        file_path = "test_document.md"
        document_id = "doc_123"
        
        # Mock file processing
        chunks = [
            DocumentChunk(
                id="chunk_1",
                content="Test content 1",
                metadata={"source": file_path, "chunk_index": 0},
                embedding=None
            )
        ]
        mock_document_processor.process_document.return_value = chunks
        
        # Mock embedding generation
        mock_embedding_client.embed_batch.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        
        result = rag_pipeline.add_document(file_path)
        
        assert result == document_id
        mock_document_processor.process_document.assert_called_once_with(file_path)
        mock_embedding_client.embed_batch.assert_called_once()
        mock_vector_store.add_document.assert_called_once()
    
    def test_add_document_processing_error(self, rag_pipeline, mock_document_processor):
        """Test document addition with processing error"""
        mock_document_processor.process_document.side_effect = Exception("Processing failed")
        
        with pytest.raises(Exception, match="Processing failed"):
            rag_pipeline.add_document("invalid_document.md")
    
    def test_add_document_embedding_error(self, rag_pipeline, mock_document_processor, mock_embedding_client):
        """Test document addition with embedding error"""
        chunks = [
            DocumentChunk(
                id="chunk_1",
                content="Test content",
                metadata={"source": "test.md", "chunk_index": 0},
                embedding=None
            )
        ]
        mock_document_processor.process_document.return_value = chunks
        mock_embedding_client.embed_batch.side_effect = Exception("Embedding failed")
        
        with pytest.raises(Exception, match="Embedding failed"):
            rag_pipeline.add_document("test_document.md")
    
    def test_update_document_success(self, rag_pipeline):
        """Test successful document update"""
        document_id = "doc_123"
        file_path = "updated_document.md"
        
        # Mock the update process
        with patch.object(rag_pipeline, 'delete_document') as mock_delete:
            with patch.object(rag_pipeline, 'add_document') as mock_add:
                mock_add.return_value = "doc_456"
                
                result = rag_pipeline.update_document(document_id, file_path)
                
                assert result == "doc_456"
                mock_delete.assert_called_once_with(document_id)
                mock_add.assert_called_once_with(file_path)
    
    def test_delete_document_success(self, rag_pipeline, mock_vector_store):
        """Test successful document deletion"""
        document_id = "doc_123"
        
        result = rag_pipeline.delete_document(document_id)
        
        assert result is True
        mock_vector_store.delete_document.assert_called_once_with(document_id)
    
    def test_delete_document_not_found(self, rag_pipeline, mock_vector_store):
        """Test document deletion when document not found"""
        mock_vector_store.delete_document.return_value = False
        
        result = rag_pipeline.delete_document("non_existent_doc")
        
        assert result is False
    
    def test_get_context_with_documents(self, rag_pipeline):
        """Test context generation with documents"""
        documents = [
            DocumentChunk(
                id="chunk_1",
                content="First chunk content.",
                metadata={"source": "doc1.md", "chunk_index": 0},
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
            ),
            DocumentChunk(
                id="chunk_2",
                content="Second chunk content.",
                metadata={"source": "doc2.md", "chunk_index": 0},
                embedding=[0.6, 0.7, 0.8, 0.9, 1.0]
            )
        ]
        
        context = rag_pipeline._get_context(documents)
        
        expected_context = "First chunk content.\n\nSecond chunk content."
        assert context == expected_context
    
    def test_get_context_empty_documents(self, rag_pipeline):
        """Test context generation with empty documents"""
        context = rag_pipeline._get_context([])
        assert context == ""
    
    def test_health_check_success(self, rag_pipeline, mock_embedding_client, mock_vector_store):
        """Test successful health check"""
        mock_embedding_client.health_check.return_value = {"status": "healthy"}
        mock_vector_store.health_check.return_value = {"status": "healthy"}
        
        health_status = rag_pipeline.health_check()
        
        assert health_status["status"] == "healthy"
        assert "embedding_client" in health_status
        assert "vector_store" in health_status
        assert health_status["embedding_client"]["status"] == "healthy"
        assert health_status["vector_store"]["status"] == "healthy"
    
    def test_health_check_partial_failure(self, rag_pipeline, mock_embedding_client, mock_vector_store):
        """Test health check with partial failure"""
        mock_embedding_client.health_check.return_value = {"status": "healthy"}
        mock_vector_store.health_check.side_effect = Exception("Vector store error")
        
        health_status = rag_pipeline.health_check()
        
        assert health_status["status"] == "degraded"
        assert health_status["embedding_client"]["status"] == "healthy"
        assert health_status["vector_store"]["status"] == "unhealthy"
        assert "error" in health_status["vector_store"]


class TestRAGResult:
    """Test cases for RAGResult class"""
    
    def test_rag_result_creation(self):
        """Test RAGResult object creation"""
        query = "Test query"
        documents = [
            DocumentChunk(
                id="chunk_1",
                content="Test content",
                metadata={"source": "test.md"},
                embedding=[0.1, 0.2, 0.3]
            )
        ]
        context = "Test context"
        
        result = RAGResult(query=query, documents=documents, context=context)
        
        assert result.query == query
        assert result.documents == documents
        assert result.context == context
        assert result.timestamp is not None
    
    def test_rag_result_default_values(self):
        """Test RAGResult with default values"""
        query = "Test query"
        result = RAGResult(query=query)
        
        assert result.query == query
        assert result.documents == []
        assert result.context == ""
        assert result.timestamp is not None


class TestDocumentChunk:
    """Test cases for DocumentChunk class"""
    
    def test_document_chunk_creation(self):
        """Test DocumentChunk object creation"""
        chunk_id = "chunk_123"
        content = "This is test content"
        metadata = {"source": "test.md", "chunk_index": 0}
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        chunk = DocumentChunk(
            id=chunk_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        assert chunk.id == chunk_id
        assert chunk.content == content
        assert chunk.metadata == metadata
        assert chunk.embedding == embedding
    
    def test_document_chunk_default_embedding(self):
        """Test DocumentChunk with default embedding"""
        chunk = DocumentChunk(
            id="chunk_123",
            content="Test content",
            metadata={"source": "test.md"}
        )
        
        assert chunk.embedding is None
    
    def test_document_chunk_str_representation(self):
        """Test DocumentChunk string representation"""
        chunk = DocumentChunk(
            id="chunk_123",
            content="Test content",
            metadata={"source": "test.md"}
        )
        
        str_repr = str(chunk)
        assert "chunk_123" in str_repr
        assert "Test content" in str_repr


if __name__ == "__main__":
    pytest.main([__file__])
