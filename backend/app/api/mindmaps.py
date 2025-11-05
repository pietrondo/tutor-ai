from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

router = APIRouter(prefix="/courses/{course_id}/books/{book_id}/mindmaps", tags=["mindmaps"])

class MindmapCreate(BaseModel):
    title: str
    content_markdown: str
    structured_map: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = {}

class MindmapResponse(BaseModel):
    id: str
    title: str
    content_markdown: str
    structured_map: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class MindmapListResponse(BaseModel):
    mindmaps: List[MindmapResponse]

# Data storage (in a real app, this would be a database)
MINDMAPS_DB = {}

def get_mindmaps_file_path(course_id: str, book_id: str) -> str:
    """Get the file path for storing mindmaps"""
    return f"data/courses/{course_id}/books/{book_id}/mindmaps.json"

def load_mindmaps(course_id: str, book_id: str) -> List[Dict]:
    """Load mindmaps from file"""
    file_path = get_mindmaps_file_path(course_id, book_id)

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_mindmaps(course_id: str, book_id: str, mindmaps: List[Dict]) -> None:
    """Save mindmaps to file"""
    file_path = get_mindmaps_file_path(course_id, book_id)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(mindmaps, f, ensure_ascii=False, indent=2)

@router.post("", response_model=MindmapResponse)
async def create_mindmap(course_id: str, book_id: str, mindmap: MindmapCreate):
    """
    Create a new mindmap for a book
    """
    try:
        # Load existing mindmaps
        mindmaps = load_mindmaps(course_id, book_id)

        # Generate unique ID
        mindmap_id = f"mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(mindmaps)}"

        # Create new mindmap
        new_mindmap = {
            "id": mindmap_id,
            "title": mindmap.title,
            "content_markdown": mindmap.content_markdown,
            "structured_map": mindmap.structured_map,
            "metadata": {
                **mindmap.metadata,
                "course_id": course_id,
                "book_id": book_id
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Add to list and save
        mindmaps.append(new_mindmap)
        save_mindmaps(course_id, book_id, mindmaps)

        return MindmapResponse(**new_mindmap)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mindmap: {str(e)}")

@router.get("", response_model=MindmapListResponse)
async def get_mindmaps(course_id: str, book_id: str):
    """
    Get all mindmaps for a book
    """
    try:
        mindmaps = load_mindmaps(course_id, book_id)

        # Convert to response models
        mindmap_responses = []
        for mindmap in mindmaps:
            content_markdown = mindmap.get("content_markdown") or mindmap.get("content") or ""
            structured_map = mindmap.get("structured_map") or mindmap.get("metadata", {}).get("structured_map", {})
            mindmap_responses.append(MindmapResponse(
                id=mindmap["id"],
                title=mindmap["title"],
                content_markdown=content_markdown,
                structured_map=structured_map if isinstance(structured_map, dict) else {},
                metadata=mindmap.get("metadata", {}),
                created_at=datetime.fromisoformat(mindmap["created_at"]),
                updated_at=datetime.fromisoformat(mindmap["updated_at"])
            ))

        return MindmapListResponse(mindmaps=mindmap_responses)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mindmaps: {str(e)}")

@router.get("/{mindmap_id}", response_model=MindmapResponse)
async def get_mindmap(course_id: str, book_id: str, mindmap_id: str):
    """
    Get a specific mindmap by ID
    """
    try:
        mindmaps = load_mindmaps(course_id, book_id)

        # Find the mindmap
        mindmap = None
        for m in mindmaps:
            if m["id"] == mindmap_id:
                mindmap = m
                break

        if not mindmap:
            raise HTTPException(status_code=404, detail="Mindmap not found")

        content_markdown = mindmap.get("content_markdown") or mindmap.get("content") or ""
        structured_map = mindmap.get("structured_map") or mindmap.get("metadata", {}).get("structured_map", {})

        return MindmapResponse(
            id=mindmap["id"],
            title=mindmap["title"],
            content_markdown=content_markdown,
            structured_map=structured_map if isinstance(structured_map, dict) else {},
            metadata=mindmap.get("metadata", {}),
            created_at=datetime.fromisoformat(mindmap["created_at"]),
            updated_at=datetime.fromisoformat(mindmap["updated_at"])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mindmap: {str(e)}")

@router.delete("/{mindmap_id}")
async def delete_mindmap(course_id: str, book_id: str, mindmap_id: str):
    """
    Delete a specific mindmap by ID
    """
    try:
        mindmaps = load_mindmaps(course_id, book_id)

        # Find and remove the mindmap
        original_length = len(mindmaps)
        mindmaps = [m for m in mindmaps if m["id"] != mindmap_id]

        if len(mindmaps) == original_length:
            raise HTTPException(status_code=404, detail="Mindmap not found")

        # Save updated list
        save_mindmaps(course_id, book_id, mindmaps)

        return {"success": True, "message": "Mindmap deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mindmap: {str(e)}")

@router.put("/{mindmap_id}", response_model=MindmapResponse)
async def update_mindmap(course_id: str, book_id: str, mindmap_id: str, mindmap: MindmapCreate):
    """
    Update an existing mindmap
    """
    try:
        mindmaps = load_mindmaps(course_id, book_id)

        # Find and update the mindmap
        updated = False
        for i, m in enumerate(mindmaps):
            if m["id"] == mindmap_id:
                mindmaps[i] = {
                    **m,
                    "title": mindmap.title,
                    "content_markdown": mindmap.content_markdown,
                    "structured_map": mindmap.structured_map,
                    "metadata": {
                        **mindmap.metadata,
                        "course_id": course_id,
                        "book_id": book_id
                    },
                    "updated_at": datetime.now().isoformat()
                }
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="Mindmap not found")

        # Save updated list
        save_mindmaps(course_id, book_id, mindmaps)

        # Return updated mindmap
        updated_mindmap = next(m for m in mindmaps if m["id"] == mindmap_id)

        return MindmapResponse(
            id=updated_mindmap["id"],
            title=updated_mindmap["title"],
            content_markdown=updated_mindmap.get("content_markdown") or updated_mindmap.get("content") or "",
            structured_map=updated_mindmap.get("structured_map", {}),
            metadata=updated_mindmap.get("metadata", {}),
            created_at=datetime.fromisoformat(updated_mindmap["created_at"]),
            updated_at=datetime.fromisoformat(updated_mindmap["updated_at"])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mindmap: {str(e)}")

@router.get("/status")
async def get_mindmaps_status():
    """
    Get mindmaps service status
    """
    return {
        "status": "active",
        "features": {
            "create": True,
            "read": True,
            "update": True,
            "delete": True,
            "list": True,
            "persistence": "file_based",
            "storage_format": "json"
        },
        "max_title_length": 200,
        "max_content_length": 1000000  # 1MB
    }
