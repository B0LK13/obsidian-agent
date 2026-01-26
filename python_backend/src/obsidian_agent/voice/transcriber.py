"""Audio transcription for voice notes."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_path: Path) -> str: ...


@dataclass
class TranscriptionResult:
    text: str
    duration_seconds: float
    language: str | None = None
    confidence: float = 0.0
    segments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Transcriber:
    """Transcribe audio files to text."""
    
    SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    
    def __init__(self, provider: TranscriptionProvider | None = None, model: str = "base"):
        self.provider = provider
        self.model = model
        self._whisper_available = self._check_whisper()
    
    def _check_whisper(self) -> bool:
        try:
            import whisper
            return True
        except ImportError:
            logger.warning("Whisper not available. Install with: pip install openai-whisper")
            return False
    
    def is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    async def transcribe(self, audio_path: Path) -> TranscriptionResult | None:
        """Transcribe an audio file."""
        if not self.is_supported(audio_path):
            logger.warning(f"Unsupported audio format: {audio_path.suffix}")
            return None
        
        if self.provider:
            text = await self.provider.transcribe(audio_path)
            return TranscriptionResult(text=text, duration_seconds=0)
        
        if not self._whisper_available:
            logger.error("No transcription provider available")
            return None
        
        return await self._transcribe_whisper(audio_path)
    
    async def _transcribe_whisper(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe using local Whisper model."""
        import whisper
        
        model = whisper.load_model(self.model)
        result = model.transcribe(str(audio_path))
        
        segments = [
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in result.get("segments", [])
        ]
        
        duration = segments[-1]["end"] if segments else 0
        
        return TranscriptionResult(
            text=result["text"],
            duration_seconds=duration,
            language=result.get("language"),
            segments=segments,
        )
    
    async def transcribe_to_note(self, audio_path: Path, output_path: Path) -> Path | None:
        """Transcribe audio and save as markdown note."""
        result = await self.transcribe(audio_path)
        if not result:
            return None
        
        content = f"""# {audio_path.stem}

**Source:** {audio_path.name}
**Duration:** {result.duration_seconds:.1f}s
**Language:** {result.language or 'unknown'}

---

{result.text}
"""
        output_path.write_text(content, encoding="utf-8")
        return output_path
    
    async def batch_transcribe(self, audio_dir: Path) -> list[TranscriptionResult]:
        """Transcribe all audio files in a directory."""
        results = []
        for audio_file in audio_dir.iterdir():
            if self.is_supported(audio_file):
                result = await self.transcribe(audio_file)
                if result:
                    results.append(result)
        return results
    
    def get_capabilities(self) -> dict[str, bool]:
        return {
            "local_whisper": self._whisper_available,
            "external_provider": self.provider is not None,
        }
