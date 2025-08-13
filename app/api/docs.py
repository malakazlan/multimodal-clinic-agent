"""
Documents API routes for the Healthcare Voice AI Assistant.
Handles document ingestion, management, and retrieval operations.
"""

import time
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import aiofiles

from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore
from utils.logger import logger
from config.settings import get_settings

router = APIRouter()

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()


class DocumentInfo(BaseModel):
    """Information about a document."""
    id: str
    title: str
    source: str
    file_type: str
    size_bytes: int
    uploaded_at: float
    processed_at: Optional[float] = None
    status: str  # pending, processing, completed, failed
    chunks_count: int = 0
    metadata: dict = {}


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    document_id: str
    message: str
    status: str
    estimated_processing_time: int


class DocumentSearchResult(BaseModel):
    """Result from document search."""
    document_id: str
    title: str
    source: str
    content_snippet: str
    relevance_score: float
    metadata: dict


class DocumentStats(BaseModel):
    """Document collection statistics."""
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    documents_by_type: dict
    documents_by_status: dict
    last_updated: float


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Document title"),
    source: Optional[str] = Query(None, description="Document source"),
    category: Optional[str] = Query(None, description="Document category")
):
    """
    Upload a healthcare document for processing and indexing.
    
    Args:
        file: Document file to upload
        title: Optional document title
        background_tasks: Background tasks for processing
        title: Document title
        source: Document source
        category: Document category
        
    Returns:
        DocumentUploadResponse with upload status
    """
    start_time = time.time()
    settings = get_settings()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # Generate document ID
        import uuid
        document_id = str(uuid.uuid4())
        
        # Use provided title or filename
        doc_title = title or Path(file.filename).stem
        
        # Save uploaded file
        upload_dir = Path(settings.upload_dir) / "documents"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{document_id}_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create document info
        document_info = DocumentInfo(
            id=document_id,
            title=doc_title,
            source=source or "unknown",
            file_type=Path(file.filename).suffix.lower().lstrip('.'),
            size_bytes=file.size or 0,
            uploaded_at=start_time,
            status="pending",
            metadata={
                "category": category,
                "original_filename": file.filename,
                "upload_timestamp": start_time
            }
        )
        
        # Store document info (in production, this would go to a database)
        # For now, we'll process it immediately
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            document_id,
            str(file_path),
            document_info
        )
        
        logger.info(f"Document uploaded: {document_id} - {doc_title}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            message="Document uploaded successfully and queued for processing",
            status="pending",
            estimated_processing_time=30  # seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip")
):
    """
    List uploaded documents with optional filtering.
    
    Args:
        status: Filter by document status
        category: Filter by document category
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        
    Returns:
        List of DocumentInfo objects
    """
    try:
        # This would query a database in production
        # For now, return mock data
        documents = []
        
        # Mock document data
        for i in range(min(limit, 10)):
            doc = DocumentInfo(
                id=f"doc_{i}",
                title=f"Healthcare Document {i}",
                source="medical_library",
                file_type="pdf",
                size_bytes=1024 * 1024,
                uploaded_at=time.time() - (i * 3600),
                processed_at=time.time() - (i * 3600) + 300,
                status="completed",
                chunks_count=5,
                metadata={"category": "general", "author": "Dr. Smith"}
            )
            documents.append(doc)
        
        # Apply filters
        if status:
            documents = [d for d in documents if d.status == status]
        if category:
            documents = [d for d in documents if d.metadata.get("category") == category]
        
        return documents[offset:offset + limit]
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results to return"),
    min_score: float = Query(0.5, description="Minimum relevance score")
):
    """
    Search documents using semantic similarity.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        min_score: Minimum relevance score
        
    Returns:
        List of DocumentSearchResult objects
    """
    try:
        # Perform semantic search
        search_results = await vector_store.search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )
        
        # Convert to response format
        results = []
        for doc in search_results:
            result = DocumentSearchResult(
                document_id=doc.metadata.get("document_id", "unknown"),
                title=doc.metadata.get("title", "Unknown Title"),
                source=doc.metadata.get("source", "Unknown Source"),
                content_snippet=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                relevance_score=doc.relevance_score,
                metadata=doc.metadata
            )
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Document search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document search failed")


@router.get("/stats", response_model=DocumentStats)
async def get_document_stats():
    """
    Get document collection statistics.
    
    Returns:
        DocumentStats with collection information
    """
    try:
        # This would query actual statistics in production
        # For now, return mock data
        
        stats = DocumentStats(
            total_documents=150,
            total_chunks=750,
            total_size_bytes=150 * 1024 * 1024,  # 150 MB
            documents_by_type={
                "pdf": 100,
                "docx": 30,
                "txt": 20
            },
            documents_by_status={
                "completed": 140,
                "processing": 5,
                "pending": 3,
                "failed": 2
            },
            last_updated=time.time()
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get document stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get document stats")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its associated chunks.
    
    Args:
        document_id: ID of the document to delete
    """
    try:
        # Delete from vector store
        await vector_store.delete_document(document_id)
        
        # Delete file (in production, this would also update database)
        upload_dir = Path(settings.upload_dir) / "documents"
        for file_path in upload_dir.glob(f"{document_id}_*"):
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        
        logger.info(f"Document deleted: {document_id}")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """
    Get information about a specific document.
    
    Args:
        document_id: ID of the document to retrieve
        
    Returns:
        DocumentInfo for the specified document
    """
    try:
        # This would query a database in production
        # For now, return mock data
        
        doc = DocumentInfo(
            id=document_id,
            title="Sample Healthcare Document",
            source="medical_library",
            file_type="pdf",
            size_bytes=1024 * 1024,
            uploaded_at=time.time() - 3600,
            processed_at=time.time() - 3300,
            status="completed",
            chunks_count=5,
            metadata={"category": "general", "author": "Dr. Smith"}
        )
        
        return doc
        
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get document")


async def process_document_background(document_id: str, file_path: str, document_info: DocumentInfo):
    """Process document in background task."""
    try:
        logger.info(f"Starting background processing for document: {document_id}")
        
        # Update status to processing
        document_info.status = "processing"
        
        # Process document
        chunks = await document_processor.process_document(file_path)
        
        # Add to vector store
        await vector_store.add_documents(chunks, document_id)
        
        # Update status to completed
        document_info.status = "completed"
        document_info.processed_at = time.time()
        document_info.chunks_count = len(chunks)
        
        logger.info(f"Document processing completed: {document_id} - {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {str(e)}", exc_info=True)
        document_info.status = "failed"
        document_info.metadata["error"] = str(e)
