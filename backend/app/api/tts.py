from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from services.local_tts_service import synthesize_local, synthesize_batch_local, list_recordings as list_rec_meta
from services.audio_library_service import (
    list_recordings as lib_list,
    update_recording,
    create_playlist,
    list_playlists,
    add_to_playlist,
    remove_from_playlist,
    available_voices,
    save_voice,
    list_voices,
    add_voice_sample,
)

router = APIRouter(prefix="/api/tts", tags=["tts"])

class TTSRequest(BaseModel):
    text: str
    title: Optional[str] = None
    language: str = "it"
    voice: str = "alloy"
    speed: float = 1.0
    tone: str = "neutral"
    categories: Optional[List[str]] = None
    speaker_id: Optional[str] = None

class TTSBatchItem(BaseModel):
    text: str
    title: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    tone: Optional[str] = None

class TTSBatchRequest(BaseModel):
    items: List[TTSBatchItem]

class RecordingUpdate(BaseModel):
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    language: Optional[str] = None

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.get("/voices")
def voices() -> List[Dict[str, Any]]:
    base = available_voices()
    custom = list_voices()
    return base + [{"id": v["id"], "name": f"{v['name']} ({v['sample_count']})", "language": v.get("language", "it")} for v in custom]

@router.get("/voices/custom")
def voices_custom_list() -> List[Dict[str, Any]]:
    return list_voices()

@router.post("/voices/custom")
async def voices_custom_upload(file: UploadFile = File(...), name: str = Form(...), language: str = Form("it")) -> Dict[str, Any]:
    try:
        data = await file.read()
        return save_voice(data, file.filename, name, language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voices/custom/{voice_id}/samples")
async def voices_custom_add_sample(voice_id: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        data = await file.read()
        res = add_voice_sample(voice_id, data, file.filename)
        if not res:
            raise HTTPException(status_code=404, detail="Voce non trovata")
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize")
def synthesize(req: TTSRequest) -> Dict[str, Any]:
    try:
        rec = synthesize_local(req.text, req.title, req.language, req.voice, req.speed, req.tone, req.speaker_id)
        if req.categories:
            update_recording(rec["id"], {"categories": req.categories})
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize/batch")
def synthesize_batch_api(req: TTSBatchRequest) -> List[Dict[str, Any]]:
    try:
        return synthesize_batch_local([i.model_dump() for i in req.items])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recordings")
def recordings(q: Optional[str] = Query(None), language: Optional[str] = Query(None), category: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    return lib_list({"q": q, "language": language, "category": category})

@router.put("/recordings/{recording_id}")
def recordings_update(recording_id: str, req: RecordingUpdate) -> Dict[str, Any]:
    updated = update_recording(recording_id, {k: v for k, v in req.model_dump().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=404, detail="Registrazione non trovata")
    return updated

@router.post("/playlists")
def playlists_create(req: PlaylistCreate) -> Dict[str, Any]:
    return create_playlist(req.name, req.description)

@router.get("/playlists")
def playlists_list() -> List[Dict[str, Any]]:
    return list_playlists()

@router.post("/playlists/{playlist_id}/items/{recording_id}")
def playlists_add_item(playlist_id: str, recording_id: str) -> Dict[str, Any]:
    updated = add_to_playlist(playlist_id, recording_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Playlist non trovata")
    return updated

@router.delete("/playlists/{playlist_id}/items/{recording_id}")
def playlists_remove_item(playlist_id: str, recording_id: str) -> Dict[str, Any]:
    updated = remove_from_playlist(playlist_id, recording_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Playlist non trovata")
    return updated
