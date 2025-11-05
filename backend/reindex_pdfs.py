#!/usr/bin/env python3
"""
Script to re-index existing PDF documents for a course
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append('/app')

from services.rag_service import RAGService

async def reindex_course_pdfs(course_id: str):
    """Re-index all PDF files for a specific course"""

    # Initialize RAG service
    rag_service = RAGService()

    # Path to course directory
    course_dir = Path(f"/app/data/courses/{course_id}")

    if not course_dir.exists():
        print(f"Course directory not found: {course_dir}")
        return False

    print(f"Re-indexing PDFs for course: {course_id}")

    # Find all PDF files in the course directory
    pdf_files = list(course_dir.rglob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in course directory")
        return False

    print(f"Found {len(pdf_files)} PDF files to index")

    success_count = 0

    for pdf_file in pdf_files:
        try:
            print(f"Indexing: {pdf_file.name}")

            # Extract book_id from path if available
            path_parts = pdf_file.parts
            book_id = None

            # Look for book_id in path (usually parent directory of PDF)
            for part in reversed(path_parts):
                if len(part) == 36 and '-' in part:  # UUID format
                    book_id = part
                    break

            # Index the PDF
            await rag_service.index_pdf(str(pdf_file), course_id, book_id)
            print(f"✅ Successfully indexed: {pdf_file.name}")
            success_count += 1

        except Exception as e:
            print(f"❌ Error indexing {pdf_file.name}: {e}")

    print(f"\nIndexing complete: {success_count}/{len(pdf_files)} files indexed successfully")

    # Get collection stats
    stats = rag_service.get_collection_stats()
    print(f"Total documents in collection: {stats['total_documents']}")

    return success_count > 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reindex_pdfs.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    try:
        result = asyncio.run(reindex_course_pdfs(course_id))
        if result:
            print("✅ Re-indexing completed successfully")
        else:
            print("❌ Re-indexing failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error during re-indexing: {e}")
        sys.exit(1)