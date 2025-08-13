"""
RAG Pipeline for the Healthcare Voice AI Assistant.
Orchestrates document retrieval, embedding, and context generation.
"""

import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger

from .vector_store import VectorStore
from .embedding_client import EmbeddingClient
from .document_processor import DocumentProcessor
from config.settings import get_settings


@dataclass
class RAGResult:
    """Result from RAG pipeline query."""
    documents: List['DocumentChunk']
    query: str
    total_results: int
    processing_time: float
    metadata: Dict[str, Any] = None


@dataclass
class DocumentChunk:
    """A chunk of document content with metadata."""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    chunk_id: str
    document_id: str


class RAGPipeline:
    """Main RAG pipeline for document retrieval and context generation."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_client = EmbeddingClient()
        self.document_processor = DocumentProcessor()
        self.settings = get_settings()
        
        logger.info("RAG Pipeline initialized")
    
    async def query(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None,
        filters: Dict[str, Any] = None,
        include_metadata: bool = True
    ) -> RAGResult:
        """
        Query the RAG pipeline for relevant documents.
        
        Args:
            query: User query text
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
            filters: Additional filters for search
            include_metadata: Whether to include document metadata
            
        Returns:
            RAGResult with relevant documents and metadata
        """
        start_time = time.time()
        
        try:
            # Use settings defaults if not provided
            top_k = top_k or self.settings.top_k_results
            similarity_threshold = similarity_threshold or self.settings.similarity_threshold
            
            logger.debug(f"RAG query: '{query}' with top_k={top_k}, threshold={similarity_threshold}")
            
            # Generate query embedding
            query_embedding = await self.embedding_client.embed_text(query)
            
            # Search vector store
            search_results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                filters=filters
            )
            
            # Process and filter results
            processed_results = []
            for result in search_results:
                if result.relevance_score >= similarity_threshold:
                    chunk = DocumentChunk(
                        content=result.content,
                        metadata=result.metadata if include_metadata else {},
                        relevance_score=result.relevance_score,
                        chunk_id=result.chunk_id,
                        document_id=result.document_id
                    )
                    processed_results.append(chunk)
            
            # Sort by relevance score
            processed_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            processing_time = time.time() - start_time
            
            logger.info(f"RAG query completed: {len(processed_results)} results in {processing_time:.3f}s")
            
            return RAGResult(
                documents=processed_results,
                query=query,
                total_results=len(processed_results),
                processing_time=processing_time,
                metadata={
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold,
                    "filters_applied": filters or {},
                    "embedding_model": self.settings.embedding_model
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"RAG query failed: {str(e)}", exc_info=True)
            raise
    
    async def add_documents(
        self,
        documents: List[str],
        metadata: Dict[str, Any] = None,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> bool:
        """
        Add new documents to the RAG pipeline.
        
        Args:
            documents: List of document content strings
            metadata: Document metadata
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use settings defaults if not provided
            chunk_size = chunk_size or self.settings.chunk_size
            chunk_overlap = chunk_overlap or self.settings.chunk_overlap
            
            logger.info(f"Adding {len(documents)} documents to RAG pipeline")
            
            # Process documents into chunks
            all_chunks = []
            for i, doc_content in enumerate(documents):
                chunks = self.document_processor.chunk_text(
                    text=doc_content,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                # Add metadata to chunks
                for j, chunk in enumerate(chunks):
                    chunk_metadata = {
                        "document_index": i,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                        **(metadata or {})
                    }
                    
                    all_chunks.append({
                        "content": chunk,
                        "metadata": chunk_metadata
                    })
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk["content"] for chunk in all_chunks]
            embeddings = await self.embedding_client.embed_batch(chunk_texts)
            
            # Add to vector store
            success = await self.vector_store.add_documents_with_embeddings(
                documents=all_chunks,
                embeddings=embeddings
            )
            
            if success:
                logger.info(f"Successfully added {len(all_chunks)} chunks to vector store")
            else:
                logger.error("Failed to add documents to vector store")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add documents to RAG pipeline: {str(e)}", exc_info=True)
            return False
    
    async def update_document(
        self,
        document_id: str,
        new_content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update an existing document in the RAG pipeline.
        
        Args:
            document_id: ID of the document to update
            new_content: New document content
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating document: {document_id}")
            
            # Remove old document
            await self.vector_store.delete_document(document_id)
            
            # Add updated document
            success = await self.add_documents(
                documents=[new_content],
                metadata=metadata or {"document_id": document_id}
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}", exc_info=True)
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the RAG pipeline.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deleting document: {document_id}")
            
            success = await self.vector_store.delete_document(document_id)
            
            if success:
                logger.info(f"Successfully deleted document: {document_id}")
            else:
                logger.warning(f"Document {document_id} not found in vector store")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}", exc_info=True)
            return False
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        try:
            vector_store_stats = await self.vector_store.get_stats()
            
            stats = {
                "total_documents": vector_store_stats.get("total_documents", 0),
                "total_chunks": vector_store_stats.get("total_chunks", 0),
                "embedding_dimensions": vector_store_stats.get("embedding_dimensions", 0),
                "index_size_mb": vector_store_stats.get("index_size_mb", 0),
                "last_updated": vector_store_stats.get("last_updated", time.time()),
                "embedding_model": self.settings.embedding_model,
                "chunk_size": self.settings.chunk_size,
                "chunk_overlap": self.settings.chunk_overlap
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get pipeline stats: {str(e)}", exc_info=True)
            return {}
    
    async def health_check(self) -> bool:
        """
        Perform health check on RAG pipeline components.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check vector store
            vector_store_healthy = await self.vector_store.health_check()
            
            # Check embedding client
            embedding_healthy = await self.embedding_client.health_check()
            
            overall_healthy = vector_store_healthy and embedding_healthy
            
            logger.info(f"RAG pipeline health check: {'healthy' if overall_healthy else 'unhealthy'}")
            
            return overall_healthy
            
        except Exception as e:
            logger.error(f"RAG pipeline health check failed: {str(e)}", exc_info=True)
            return False
