from __future__ import annotations

from pathlib import Path


class LocalAudioTranscriber:
    def transcribe(self, audio_path: Path) -> dict:
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(str(audio_path), beam_size=5)
            text = " ".join(segment.text.strip() for segment in segments)
            return {
                "text": text,
                "language": info.language,
                "duration": info.duration,
                "confidence": getattr(info, "language_probability", None),
            }
        except Exception:
            return {
                "text": "",
                "language": "unknown",
                "duration": None,
                "confidence": None,
                "note": "Install the multimodal extras to enable faster-whisper transcription.",
            }

