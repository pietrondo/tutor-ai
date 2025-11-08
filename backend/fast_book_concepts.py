#!/usr/bin/env python3
"""
Fast book concept maps API endpoint - bypasses RAG for performance
"""

import json
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

class BookConceptRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None

def get_book_concepts_fast(request: BookConceptRequest):
    """Get book concepts directly from stored data without RAG processing"""
    try:
        # Load concept maps
        concept_maps_path = Path("data/concept_maps.json")

        if not concept_maps_path.exists():
            raise HTTPException(status_code=404, detail="Concept maps not found")

        with open(concept_maps_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        course_id = request.course_id
        book_id = request.book_id

        if course_id not in data.get("concept_maps", {}):
            raise HTTPException(status_code=404, detail="Course not found")

        course_data = data["concept_maps"][course_id]

        # If book_id is specified, return only that book's concepts
        if book_id:
            if "books" not in course_data or book_id not in course_data["books"]:
                raise HTTPException(status_code=404, detail="Book concepts not found")

            book_data = course_data["books"][book_id]
            return JSONResponse(content={
                "success": True,
                "course_id": course_id,
                "book_id": book_id,
                "book_title": book_data.get("book_title", "Unknown"),
                "concepts": book_data.get("concepts", []),
                "total_concepts": len(book_data.get("concepts", [])),
                "generated_at": book_data.get("generated_at")
            })

        # If no book_id, return all books
        if "books" not in course_data:
            return JSONResponse(content={
                "success": False,
                "message": "No book concepts found for this course",
                "books": {}
            })

        books_summary = {}
        for book_id, book_data in course_data["books"].items():
            books_summary[book_id] = {
                "book_title": book_data.get("book_title", "Unknown"),
                "concepts_count": len(book_data.get("concepts", [])),
                "generated_at": book_data.get("generated_at")
            }

        return JSONResponse(content={
            "success": True,
            "course_id": course_id,
            "course_name": course_data.get("course_name", "Unknown"),
            "total_books": len(course_data["books"]),
            "books": books_summary
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))