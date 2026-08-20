"""
Server-side speech-to-text. Optional by design: the frontend already uses
the browser's Web Speech API for the primary voice flow, so this only
matters for the /transcribe endpoint (audio uploaded as base64). If
faster-whisper isn't installed or fails to load, using_whisper is False and
app.py's /transcribe route falls back to reporting that browser
transcription should be used instead — it never crashes either way.
"""


class SpeechToTextService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.using_whisper = False
        self._model = None

        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.using_whisper = True
        except Exception as exc:  # noqa: BLE001 - intentional graceful degrade
            print(f"[SpeechToTextService] faster-whisper unavailable, server-side STT disabled. Reason: {exc}")

    def transcribe(self, audio_path: str) -> str:
        if not self.using_whisper or self._model is None:
            return ""
        segments, _ = self._model.transcribe(audio_path, beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()
