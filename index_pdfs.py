#!/usr/bin/env python3
"""
Script to index existing PDF files into the vector database
"""

import os
import sys
import asyncio
from pathlib import Path
import structlog

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.rag_service import RAGService

logger = structlog.get_logger()

async def index_existing_pdfs():
    """Index all existing PDF files into the vector database"""

    data_dir = Path("data")
    rag_service = RAGService()

    indexed_count = 0
    error_count = 0

    # Find all PDF files
    pdf_files = list(data_dir.rglob("*.pdf"))

    if not pdf_files:
        logger.warning("No PDF files found in data directory")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to index")

    for pdf_path in pdf_files:
        try:
            # Extract course_id and book_id from path
            path_parts = pdf_path.parts

            course_id = None
            book_id = None

            for part in path_parts:
                if len(part) == 36 and part.count('-') == 4:  # UUID format
                    if not course_id:
                        course_id = part
                    elif not book_id:
                        book_id = part

            if not course_id:
                logger.warning(f"Could not extract course_id from path: {pdf_path}")
                continue

            if not book_id:
                logger.warning(f"Could not extract book_id from path: {pdf_path}")
                continue

            logger.info(f"Indexing PDF: {pdf_path.name}")
            logger.info(f"  Course ID: {course_id}")
            logger.info(f"  Book ID: {book_id}")

            # Index the PDF
            await rag_service.index_pdf(
                file_path=str(pdf_path),
                course_id=course_id,
                book_id=book_id
            )

            indexed_count += 1
            logger.info(f"Successfully indexed: {pdf_path.name}")

        except Exception as e:
            error_count += 1
            logger.error(f"Failed to index PDF {pdf_path}: {e}")

    logger.info(f"Indexing complete. Success: {indexed_count}, Errors: {error_count}")

    # Test the RAG service
    if indexed_count > 0:
        logger.info("Testing RAG service...")

        test_query = "Evoluzione Storica"
        test_course = "e9195d61-9bd2-4e30-a183-cee2ab80f1b9"
        test_book = "15327ff3-5143-4361-a215-3d8abffc2310"

        try:
            result = await rag_service.retrieve_context(
                query=test_query,
                course_id=test_course,
                book_id=test_book,
                k=3
            )

            logger.info(f"RAG test result:")
            logger.info(f"  Context length: {len(result.get('text', ''))}")
            logger.info(f"  Sources found: {len(result.get('sources', []))}")
            logger.info(f"  Sample context: {result.get('text', '')[:200]}...")

        except Exception as e:
            logger.error(f"RAG test failed: {e}")

if __name__ == "__main__":
    asyncio.run(index_existing_pdfs())