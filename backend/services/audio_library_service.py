import os
import json
import uuid
from typing import List, Dict, Any, Optional

import io
from pydub import AudioSegment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.join(ROOT_DIR, "data", "audio")
VOICE_DIR = os.path.join(BASE_DIR, "voices")
VOICES_PATH = os.path.join(BASE_DIR, "voices.json")
RECORDINGS_PATH = os.path.join(BASE_DIR, "recordings.json")
PLAYLISTS_PATH = os.path.join(BASE_DIR, "playlists.json")

def _ensure_dirs():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(VOICE_DIR, exist_ok=True)

def _load_json(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path: str, data: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_recording(recording_id: str, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    _ensure_dirs()
    items = _load_json(RECORDINGS_PATH)
    for i in range(len(items)):
        if items[i].get("id") == recording_id:
            items[i].update(update)
            _save_json(RECORDINGS_PATH, items)
            return items[i]
    return None

def list_recordings(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    _ensure_dirs()
    items = _load_json(RECORDINGS_PATH)
    if not filters:
        return items
    def match(item: Dict[str, Any]) -> bool:
        q = filters.get("q")
        language = filters.get("language")
        category = filters.get("category")
        if q and q.lower() not in (item.get("title", "") + " " + item.get("text_preview", "")).lower():
            return False
        if language and item.get("language") != language:
            return False
        if category and category not in item.get("categories", []):
            return False
        return True
    return [i for i in items if match(i)]

def create_playlist(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    _ensure_dirs()
    playlists = _load_json(PLAYLISTS_PATH)
    pid = str(uuid.uuid4())
    pl = {"id": pid, "name": name, "description": description or "", "items": []}
    playlists.append(pl)
    _save_json(PLAYLISTS_PATH, playlists)
    return pl

def list_playlists() -> List[Dict[str, Any]]:
    _ensure_dirs()
    return _load_json(PLAYLISTS_PATH)

def add_to_playlist(playlist_id: str, recording_id: str) -> Optional[Dict[str, Any]]:
    _ensure_dirs()
    playlists = _load_json(PLAYLISTS_PATH)
    for i in range(len(playlists)):
        if playlists[i].get("id") == playlist_id:
            items = playlists[i].get("items", [])
            if recording_id not in items:
                items.append(recording_id)
            playlists[i]["items"] = items
            _save_json(PLAYLISTS_PATH, playlists)
            return playlists[i]
    return None

def remove_from_playlist(playlist_id: str, recording_id: str) -> Optional[Dict[str, Any]]:
    _ensure_dirs()
    playlists = _load_json(PLAYLISTS_PATH)
    for i in range(len(playlists)):
        if playlists[i].get("id") == playlist_id:
            items = [rid for rid in playlists[i].get("items", []) if rid != recording_id]
            playlists[i]["items"] = items
            _save_json(PLAYLISTS_PATH, playlists)
            return playlists[i]
    return None

def available_voices() -> List[Dict[str, Any]]:
    return [
        {"id": "alloy", "name": "Alloy", "language": "it"},
        {"id": "verse", "name": "Verse", "language": "it"},
        {"id": "aria", "name": "Aria", "language": "it"}
    ]

def save_voice(file_bytes: bytes, filename: str, name: str, language: str = "it") -> Dict[str, Any]:
    _ensure_dirs()
    vid = str(uuid.uuid4())
    raw = io.BytesIO(file_bytes)
    try:
        audio = AudioSegment.from_file(raw)
    except Exception:
        audio = AudioSegment.from_file(raw, format=filename.split(".")[-1].lower())
    wav_path = os.path.join(VOICE_DIR, f"{vid}.wav")
    audio.export(wav_path, format="wav")
    voices = _load_json(VOICES_PATH)
    meta = {"id": vid, "name": name, "language": language, "samples": [wav_path]}
    voices.append(meta)
    _save_json(VOICES_PATH, voices)
    return meta

def list_voices() -> List[Dict[str, Any]]:
    _ensure_dirs()
    voices = _load_json(VOICES_PATH)
    normalized = []
    for v in voices:
        samples = v.get("samples") or ([v.get("file_path")] if v.get("file_path") else [])
        normalized.append({
            "id": v.get("id"),
            "name": v.get("name"),
            "language": v.get("language", "it"),
            "samples": samples,
            "sample_count": len(samples)
        })
    return normalized

def get_voice_samples(voice_id: str) -> List[str]:
    voices = _load_json(VOICES_PATH)
    for v in voices:
        if v.get("id") == voice_id:
            samples = v.get("samples") or ([v.get("file_path")] if v.get("file_path") else [])
            return [s for s in samples if s]
    return []

def add_voice_sample(voice_id: str, file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
    _ensure_dirs()
    raw = io.BytesIO(file_bytes)
    try:
        audio = AudioSegment.from_file(raw)
    except Exception:
        audio = AudioSegment.from_file(raw, format=filename.split(".")[-1].lower())
    sample_id = str(uuid.uuid4())
    wav_path = os.path.join(VOICE_DIR, f"{voice_id}_{sample_id}.wav")
    audio.export(wav_path, format="wav")
    voices = _load_json(VOICES_PATH)
    for i in range(len(voices)):
        if voices[i].get("id") == voice_id:
            samples = voices[i].get("samples") or []
            if not samples and voices[i].get("file_path"):
                samples = [voices[i]["file_path"]]
                voices[i].pop("file_path", None)
            samples.append(wav_path)
            voices[i]["samples"] = samples
            _save_json(VOICES_PATH, voices)
            return {"id": voice_id, "added": wav_path, "sample_count": len(samples)}
    return None
