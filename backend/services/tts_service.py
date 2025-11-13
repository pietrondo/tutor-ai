import os
import uuid
import json
import unicodedata
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AUDIO_DIR = os.path.join(ROOT_DIR, "data", "audio")
METADATA_PATH = os.path.join(AUDIO_DIR, "recordings.json")

def _ensure_dirs():
    os.makedirs(AUDIO_DIR, exist_ok=True)

def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def _save_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_dirs()
    data: List[Dict[str, Any]] = []
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(entry)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return entry

def list_recordings(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(METADATA_PATH):
        return []
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not filters:
        return items
    def match(item: Dict[str, Any]) -> bool:
        q = filters.get("q")
        lang = filters.get("language")
        cat = filters.get("category")
        if q and q.lower() not in (item.get("title", "") + " " + item.get("text_preview", "")).lower():
            return False
        if lang and item.get("language") != lang:
            return False
        if cat and cat not in item.get("categories", []):
            return False
        return True
    return [i for i in items if match(i)]

def synthesize_openai(text: str, title: Optional[str] = None, language: str = "it", voice: str = "alloy", speed: float = 1.0, tone: str = "neutral") -> Dict[str, Any]:
    _ensure_dirs()
    normalized = _normalize_text(text)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY mancante")
    payload = {
        "model": os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        "input": normalized,
        "voice": voice,
        "format": "mp3",
        "language": language
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/audio/speech"
    r = requests.post(url, headers=headers, json=payload, stream=True)
    if r.status_code != 200:
        raise RuntimeError(f"Errore TTS OpenAI: {r.status_code} {r.text}")
    rec_id = str(uuid.uuid4())
    filename = f"{rec_id}.mp3"
    file_path = os.path.join(AUDIO_DIR, filename)
    with open(file_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    entry = {
        "id": rec_id,
        "title": title or (normalized[:60] + ("..." if len(normalized) > 60 else "")),
        "language": language,
        "voice": voice,
        "speed": speed,
        "tone": tone,
        "filename": filename,
        "file_path": file_path,
        "url": f"/audio/{filename}",
        "duration": None,
        "bitrate": None,
        "sample_rate": None,
        "text_preview": normalized[:200],
        "categories": [],
        "created_at": datetime.utcnow().isoformat()
    }
    return _save_metadata(entry)

def synthesize_batch(items: List[Dict[str, Any]], language: str = "it", voice: str = "alloy") -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in items:
        res = synthesize_openai(
            text=item.get("text", ""),
            title=item.get("title"),
            language=item.get("language", language),
            voice=item.get("voice", voice),
            speed=float(item.get("speed", 1.0)),
            tone=item.get("tone", "neutral")
        )
        results.append(res)
    return results
