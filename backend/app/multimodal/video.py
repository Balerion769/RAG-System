from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import settings


def save_video_upload(session_id: str, filename: str, content: bytes) -> tuple[Path, dict]:
    safe_name = sanitize_filename(filename)
    target = settings.data_dir / "videos" / f"{session_id}-{uuid.uuid4().hex}-{safe_name}"
    target.write_bytes(content)
    metrics = analyze_video_placeholder(target)
    return target, metrics


def analyze_video_placeholder(path: Path) -> dict:
    size_mb = path.stat().st_size / (1024 * 1024)
    return {
        "file_size_mb": round(size_mb, 2),
        "status": "stored",
        "coachability_scope": [
            "speaking pace after transcription",
            "filler-word rate after transcription",
            "answer structure",
            "camera/audio technical quality",
        ],
        "excluded_inferences": [
            "emotion",
            "personality",
            "identity",
            "health",
            "protected traits",
        ],
    }


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name or "interview.webm"
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", name)

