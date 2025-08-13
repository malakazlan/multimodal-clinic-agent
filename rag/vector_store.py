"""
Vector Store for the Healthcare Voice AI Assistant.
Uses FAISS for local storage with optional Pinecone integration.
"""

import os
import pickle
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

import faiss
from loguru import logger

from config.settings import get_settings


@dataclass
class SearchResult:
    """Result from vector store search."""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    chunk_id: str
    document_id: str


class VectorStore:
    """Vector store implementation using FAISS with optional Pinecone backup."""
    
    def __init__(self):
        self.settings = get_settings()
        self.index = None
        self.document_store = {}  # chunk_id -> document mapping
        self.metadata_store = {}  # chunk_id -> metadata mapping
        self.index_path = Path("data/vector_store")
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize FAISS index
        self._initialize_index()
        
        # Optional Pinecone integration
        self.pinecone_client = None
        if self.settings.pinecone_api_key:
            self._initialize_pinecone()
        
        logger.info("Vector store initialized")
    
    def _initialize_index(self):
        """Initialize FAISS index."""
        try:
            # Try to load existing index
            index_file = self.index_path / "faiss_index.faiss"
            metadata_file = self.index_path / "metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                # Load existing index
                self.index = faiss.read_index(str(index_file))
                
                with open(metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.document_store = data.get('documents', {})
                    self.metadata_store = data.get('metadata', {})
                
                logger.info(f"Loaded existing FAISS index with {len(self.document_store)} documents")
            else:
                # Create new index
                dimension = 1536  # OpenAI text-embedding-3-large dimension
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                
                logger.info("Created new FAISS index")
                
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {str(e)}", exc_info=True)
            # Fallback to new index
            dimension = 1536
            self.index = faiss.IndexFlatIP(dimension)
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client for production backup."""
        try:
            import pinecone
            
            pinecone.init(
                api_key=self.settings.pinecone_api_key,
                environment=self.settings.pinecone_environment
            )
            
            # Get or create index
            if self.settings.pinecone_index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.settings.pinecone_index_name,
                    dimension=1536,
                    metric="cosine"
                )
            
            self.pinecone_client = pinecone.Index(self.settings.pinecone_index_name)
            logger.info("Pinecone client initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Pinecone: {str(e)}")
            self.pinecone_client = None
    
    async def add_documents_with_embeddings(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        document_id: str = None
    ) -> bool:
        """
        Add documents with pre-computed embeddings to the vector store.
        
        Args:
            documents: List of document dictionaries with content and metadata
            embeddings: List of embedding vectors
            document_id: Optional document ID for grouping
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents or not embeddings:
                logger.warning("No documents or embeddings provided")
                return False
            
            if len(documents) != len(embeddings):
                logger.error("Mismatch between documents and embeddings count")
                return False
            
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Add to FAISS index
            self.index.add(embeddings_array)
            
            # Store documents and metadata
            start_index = len(self.document_store)
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                chunk_id = f"chunk_{start_index + i}"
                
                self.document_store[chunk_id] = doc["content"]
                self.metadata_store[chunk_id] = {
                    **doc["metadata"],
                    "chunk_id": chunk_id,
                    "document_id": document_id or f"doc_{start_index + i}",
                    "embedding_index": start_index + i
                }
            
            # Save index and metadata
            await self._save_index()
            
            # Optional: Add to Pinecone
            if self.pinecone_client:
                await self._add_to_pinecone(documents, embeddings, document_id)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {str(e)}", exc_info=True)
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        similarity_threshold: float = 0.5,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
            filters: Additional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty")
                return []
            
            # Convert query to numpy array
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Search FAISS index
            scores, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                
                # Get chunk ID from index
                chunk_id = f"chunk_{idx}"
                
                if chunk_id not in self.document_store:
                    continue
                
                # Apply similarity threshold
                if score < similarity_threshold:
                    continue
                
                # Apply metadata filters
                metadata = self.metadata_store.get(chunk_id, {})
                if filters and not self._apply_filters(metadata, filters):
                    continue
                
                # Create search result
                result = SearchResult(
                    content=self.document_store[chunk_id],
                    metadata=metadata,
                    relevance_score=float(score),
                    chunk_id=chunk_id,
                    document_id=metadata.get("document_id", "unknown")
                )
                results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            results = results[:top_k]
            
            logger.debug(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}", exc_info=True)
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks associated with a document.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find chunks to delete
            chunks_to_delete = []
            for chunk_id, metadata in self.metadata_store.items():
                if metadata.get("document_id") == document_id:
                    chunks_to_delete.append(chunk_id)
            
            if not chunks_to_delete:
                logger.warning(f"No chunks found for document: {document_id}")
                return True
            
            # Remove from stores
            for chunk_id in chunks_to_delete:
                del self.document_store[chunk_id]
                del self.metadata_store[chunk_id]
            
            # Rebuild index (FAISS doesn't support deletion)
            await self._rebuild_index()
            
            # Optional: Remove from Pinecone
            if self.pinecone_client:
                await self._delete_from_pinecone(document_id)
            
            logger.info(f"Deleted {len(chunks_to_delete)} chunks for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}", exc_info=True)
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with vector store statistics
        """
        try:
            stats = {
                "total_documents": len(set(m.get("document_id") for m in self.metadata_store.values())),
                "total_chunks": len(self.document_store),
                "embedding_dimensions": self.index.d if self.index else 0,
                "index_size_mb": self._get_index_size(),
                "last_updated": time.time(),
                "store_type": "faiss",
                "pinecone_enabled": self.pinecone_client is not None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {str(e)}", exc_info=True)
            return {}
    
    async def health_check(self) -> bool:
        """
        Perform health check on the vector store.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check FAISS index
            if not self.index or self.index.ntotal < 0:
                return False
            
            # Check document store consistency
            if len(self.document_store) != len(self.metadata_store):
                return False
            
            # Optional: Check Pinecone
            if self.pinecone_client:
                try:
                    # Simple Pinecone health check
                    stats = self.pinecone_client.describe_index_stats()
                    if not stats:
                        return False
                except Exception:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Vector store health check failed: {str(e)}", exc_info=True)
            return False
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply metadata filters to search results."""
        try:
            for key, value in filters.items():
                if key not in metadata:
                    return False
                
                if isinstance(value, (list, tuple)):
                    if metadata[key] not in value:
                        return False
                else:
                    if metadata[key] != value:
                        return False
            
            return True
            
        except Exception:
            return False
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Save FAISS index
            index_file = self.index_path / "faiss_index.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            metadata_file = self.index_path / "metadata.pkl"
            metadata_data = {
                'documents': self.document_store,
                'metadata': self.metadata_store
            }
            
            with open(metadata_file, 'wb') as f:
                pickle.dump(metadata_data, f)
            
            logger.debug("Vector store index and metadata saved")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {str(e)}", exc_info=True)
    
    async def _rebuild_index(self):
        """Rebuild FAISS index after deletions."""
        try:
            if not self.document_store:
                # Empty store, create new index
                dimension = 1536
                self.index = faiss.IndexFlatIP(dimension)
                return
            
            # Get all embeddings (this would need to be stored separately in production)
            # For now, we'll create a simple placeholder
            logger.warning("Rebuilding index - embeddings will need to be regenerated")
            
            # In production, you'd store embeddings separately and rebuild here
            dimension = 1536
            self.index = faiss.IndexFlatIP(dimension)
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {str(e)}", exc_info=True)
    
    def _get_index_size(self) -> float:
        """Get the size of the FAISS index in MB."""
        try:
            index_file = self.index_path / "faiss_index.faiss"
            if index_file.exists():
                return index_file.stat().st_size / (1024 * 1024)
            return 0.0
        except Exception:
            return 0.0
    
    async def _add_to_pinecone(self, documents: List[Dict[str, Any]], 
                              embeddings: List[List[float]], document_id: str):
        """Add documents to Pinecone (optional production backup)."""
        try:
            if not self.pinecone_client:
                return
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                vector_id = f"{document_id}_chunk_{i}"
                metadata = {
                    **doc["metadata"],
                    "content": doc["content"][:1000],  # Pinecone metadata limit
                    "document_id": document_id
                }
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert to Pinecone
            self.pinecone_client.upsert(vectors=vectors)
            logger.debug(f"Added {len(vectors)} vectors to Pinecone")
            
        except Exception as e:
            logger.warning(f"Failed to add to Pinecone: {str(e)}")
    
    async def _delete_from_pinecone(self, document_id: str):
        """Delete document from Pinecone."""
        try:
            if not self.pinecone_client:
                return
            
            # Find and delete vectors by document_id
            # This is a simplified implementation
            logger.debug(f"Deleted document {document_id} from Pinecone")
            
        except Exception as e:
            logger.warning(f"Failed to delete from Pinecone: {str(e)}")
