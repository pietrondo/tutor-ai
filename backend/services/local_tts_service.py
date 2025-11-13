import os
import uuid
import json
import unicodedata
from typing import List, Dict, Any, Optional
from datetime import datetime

from TTS.api import TTS
from pydub import AudioSegment
from services.audio_library_service import get_voice_samples

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AUDIO_DIR = os.path.join(ROOT_DIR, "data", "audio")
METADATA_PATH = os.path.join(AUDIO_DIR, "recordings.json")

MODEL_NAME = os.getenv("LOCAL_TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")

_tts = None

def _ensure_dirs():
    os.makedirs(AUDIO_DIR, exist_ok=True)

def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def _get_tts():
    global _tts
    if _tts is None:
        _tts = TTS(MODEL_NAME)
        try:
            _tts.to("cuda")
        except Exception:
            pass
    return _tts

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

def synthesize_local(text: str, title: Optional[str] = None, language: str = "it", voice: str = "default", speed: float = 1.0, tone: str = "neutral", speaker_id: Optional[str] = None) -> Dict[str, Any]:
    _ensure_dirs()
    normalized = _normalize_text(text)
    rec_id = str(uuid.uuid4())
    wav_path = os.path.join(AUDIO_DIR, f"{rec_id}.wav")
    mp3_path = os.path.join(AUDIO_DIR, f"{rec_id}.mp3")

    tts = _get_tts()
    speaker_wavs: Optional[List[str]] = None
    if speaker_id:
        samples = get_voice_samples(speaker_id)
        if samples:
            speaker_wavs = samples
    if speaker_wavs:
        tts.tts_to_file(text=normalized, file_path=wav_path, language=language, speaker_wav=speaker_wavs)
    else:
        tts.tts_to_file(text=normalized, file_path=wav_path, language=language)

    audio = AudioSegment.from_wav(wav_path)
    if speed and abs(speed - 1.0) > 1e-3:
        audio = audio.speedup(playback_speed=max(0.5, min(2.0, speed)))
    def pitch_semitones_for_tone(t: str) -> float:
        if t == "warm":
            return -1.0
        if t == "formal":
            return 1.0
        return 0.0
    ps = pitch_semitones_for_tone(tone)
    if abs(ps) > 1e-3:
        new_frame_rate = int(audio.frame_rate * (2.0 ** (ps / 12.0)))
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(audio.frame_rate)
    audio.export(mp3_path, format="mp3", bitrate="128k")
    try:
        os.remove(wav_path)
    except Exception:
        pass

    entry = {
        "id": rec_id,
        "title": title or (normalized[:60] + ("..." if len(normalized) > 60 else "")),
        "language": language,
        "voice": voice,
        "speaker_id": speaker_id,
        "speed": speed,
        "tone": tone,
        "filename": f"{rec_id}.mp3",
        "file_path": mp3_path,
        "url": f"/audio/{rec_id}.mp3",
        "duration": round(audio.duration_seconds, 3),
        "bitrate": "128k",
        "sample_rate": audio.frame_rate,
        "text_preview": normalized[:200],
        "categories": [],
        "created_at": datetime.utcnow().isoformat()
    }
    return _save_metadata(entry)

def synthesize_batch_local(items: List[Dict[str, Any]], language: str = "it", voice: str = "default") -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in items:
        res = synthesize_local(
            text=item.get("text", ""),
            title=item.get("title"),
            language=item.get("language", language),
            voice=item.get("voice", voice),
            speed=float(item.get("speed", 1.0)),
            tone=item.get("tone", "neutral")
        )
        results.append(res)
    return results
