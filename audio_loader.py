"""Task 1: Validate and load an audio file."""

from pathlib import Path


class AudioFileLoader:
    """Validates and loads an audio file from the server."""

    ALLOWED_AUDIO = [".wav", ".mp3"]

    def __init__(self, file_name):
        """Initialize the loader with the audio file path."""
        self.file_name = Path(file_name)

    def load_audio_file(self):
        """Validate the audio file and return its path."""

        if not self.file_name.exists():
            raise FileNotFoundError(
                f"Audio file does not exist: {self.file_name}"
            )

        if self.file_name.suffix.lower() not in self.ALLOWED_AUDIO:
            raise ValueError(
                f"Unsupported audio format: {self.file_name.suffix}"
            )

        if self.file_name.stat().st_size == 0:
            raise ValueError("Audio file is empty")

        return self.file_name
