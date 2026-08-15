"""Task 3: Transcribe spoken audio into text with timestamps."""

from audio_loader import AudioFileLoader
from speech_transcriber import SpeechTranscriber


class TimestampedTranscriber(SpeechTranscriber):
    """Transcribes audio and returns text with timestamps."""

    def transcribe_with_timestamps(self, audio_file):
        audio_file = AudioFileLoader(audio_file).load_audio_file()
        result = self.model.transcribe(str(audio_file), fp16=False)
        raw_segments = result.get("segments", [])

        if not raw_segments:
            raise ValueError("No speech segments were detected in the audio file")

        return [
            {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment.get("text", "").strip(),
            }
            for segment in raw_segments
        ]

    @staticmethod
    def format_time(seconds):
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes:02d}:{remaining:05.2f}"
