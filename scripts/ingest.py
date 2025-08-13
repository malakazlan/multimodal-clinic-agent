#!/usr/bin/env python3
"""
Document Ingestion Script for the Healthcare Voice AI Assistant.
Processes healthcare documents and adds them to the RAG pipeline.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.rag_pipeline import RAGPipeline
from rag.document_processor import DocumentProcessor
from utils.logger import logger, setup_logging
from config.settings import get_settings


async def ingest_documents(
    docs_path: str,
    output_dir: str = None,
    chunk_size: int = None,
    chunk_overlap: int = None,
    batch_size: int = 10,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Ingest documents from a directory into the RAG pipeline.
    
    Args:
        docs_path: Path to documents directory
        output_dir: Output directory for processed documents
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        batch_size: Number of documents to process in each batch
        dry_run: If True, only show what would be processed
        
    Returns:
        Dictionary with ingestion results
    """
    start_time = time.time()
    
    try:
        # Initialize components
        rag_pipeline = RAGPipeline()
        document_processor = DocumentProcessor()
        settings = get_settings()
        
        # Use settings defaults if not provided
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Validate input path
        docs_path = Path(docs_path)
        if not docs_path.exists():
            raise FileNotFoundError(f"Documents path not found: {docs_path}")
        
        if not docs_path.is_dir():
            raise ValueError(f"Documents path must be a directory: {docs_path}")
        
        # Setup output directory
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting document ingestion from: {docs_path}")
        logger.info(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
        
        # Find all supported documents
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.html'}
        documents = []
        
        for file_path in docs_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                documents.append(file_path)
        
        if not documents:
            logger.warning(f"No supported documents found in {docs_path}")
            return {"status": "no_documents", "total_documents": 0}
        
        logger.info(f"Found {len(documents)} documents to process")
        
        if dry_run:
            logger.info("DRY RUN MODE - No documents will be processed")
            for doc in documents:
                logger.info(f"Would process: {doc}")
            return {"status": "dry_run", "total_documents": len(documents)}
        
        # Process documents in batches
        processed_count = 0
        failed_count = 0
        total_chunks = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}: {len(batch)} documents")
            
            batch_results = await _process_document_batch(
                batch,
                document_processor,
                rag_pipeline,
                chunk_size,
                chunk_overlap,
                output_dir
            )
            
            processed_count += batch_results["processed"]
            failed_count += batch_results["failed"]
            total_chunks += batch_results["chunks"]
            
            # Progress update
            progress = min(100, (i + len(batch)) / len(documents) * 100)
            logger.info(f"Progress: {progress:.1f}% ({i + len(batch)}/{len(documents)})")
        
        # Final statistics
        processing_time = time.time() - start_time
        
        results = {
            "status": "completed",
            "total_documents": len(documents),
            "processed_documents": processed_count,
            "failed_documents": failed_count,
            "total_chunks": total_chunks,
            "processing_time": processing_time,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        
        logger.info(f"Ingestion completed in {processing_time:.2f}s")
        logger.info(f"Processed: {processed_count}, Failed: {failed_count}, Chunks: {total_chunks}")
        
        return results
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time": processing_time
        }


async def _process_document_batch(
    documents: List[Path],
    document_processor: DocumentProcessor,
    rag_pipeline: RAGPipeline,
    chunk_size: int,
    chunk_overlap: int,
    output_dir: Path = None
) -> Dict[str, Any]:
    """Process a batch of documents."""
    batch_results = {
        "processed": 0,
        "failed": 0,
        "chunks": 0
    }
    
    for doc_path in documents:
        try:
            logger.debug(f"Processing document: {doc_path.name}")
            
            # Process document
            chunks = await document_processor.process_document(str(doc_path))
            
            if not chunks:
                logger.warning(f"No chunks extracted from {doc_path.name}")
                batch_results["failed"] += 1
                continue
            
            # Save processed chunks to output directory if specified
            if output_dir:
                await _save_processed_chunks(doc_path, chunks, output_dir)
            
            # Add to RAG pipeline
            success = await rag_pipeline.add_documents(
                documents=chunks,
                metadata={
                    "source_file": str(doc_path),
                    "file_name": doc_path.name,
                    "file_size": doc_path.stat().st_size,
                    "processed_at": time.time(),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                }
            )
            
            if success:
                batch_results["processed"] += 1
                batch_results["chunks"] += len(chunks)
                logger.debug(f"Successfully processed {doc_path.name}: {len(chunks)} chunks")
            else:
                batch_results["failed"] += 1
                logger.error(f"Failed to add {doc_path.name} to RAG pipeline")
                
        except Exception as e:
            batch_results["failed"] += 1
            logger.error(f"Failed to process {doc_path.name}: {str(e)}", exc_info=True)
    
    return batch_results


async def _save_processed_chunks(
    doc_path: Path,
    chunks: List[str],
    output_dir: Path
):
    """Save processed chunks to output directory."""
    try:
        # Create subdirectory for this document
        doc_output_dir = output_dir / doc_path.stem
        doc_output_dir.mkdir(exist_ok=True)
        
        # Save chunks as individual files
        for i, chunk in enumerate(chunks):
            chunk_file = doc_output_dir / f"chunk_{i:03d}.txt"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
        
        # Save metadata
        metadata_file = doc_output_dir / "metadata.json"
        metadata = {
            "source_file": str(doc_path),
            "file_name": doc_path.name,
            "file_size": doc_path.stat().st_size,
            "chunks_count": len(chunks),
            "processed_at": time.time()
        }
        
        import json
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
            
    except Exception as e:
        logger.warning(f"Failed to save processed chunks for {doc_path.name}: {str(e)}")


async def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Ingest healthcare documents into the RAG pipeline"
    )
    
    parser.add_argument(
        "docs_path",
        help="Path to directory containing documents to ingest"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for processed documents (optional)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Size of text chunks (default: from settings)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        help="Overlap between chunks (default: from settings)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of documents to process in each batch (default: 10)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.setLevel(args.log_level)
    
    # Run ingestion
    results = await ingest_documents(
        docs_path=args.docs_path,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Print results
    if results["status"] == "completed":
        print(f"\n✅ Ingestion completed successfully!")
        print(f"   Documents processed: {results['processed_documents']}")
        print(f"   Documents failed: {results['failed_documents']}")
        print(f"   Total chunks: {results['total_chunks']}")
        print(f"   Processing time: {results['processing_time']:.2f}s")
    elif results["status"] == "dry_run":
        print(f"\n🔍 Dry run completed!")
        print(f"   Documents that would be processed: {results['total_documents']}")
    else:
        print(f"\n❌ Ingestion failed!")
        print(f"   Error: {results.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
