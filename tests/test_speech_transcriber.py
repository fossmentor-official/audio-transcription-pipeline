"""Unit tests for SpeechTranscriber with mocked Whisper."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from speech_transcriber import SpeechTranscriber


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "speech.mp3"
    path.write_bytes(b"fake audio")
    return path


def test_successful_transcription(audio_file: Path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "  Hello world  "}

    transcriber = SpeechTranscriber(model=mock_model)
    text = transcriber.transcribe(audio_file)

    assert text == "Hello world"
    mock_model.transcribe.assert_called_once_with(str(audio_file), fp16=False)


def test_no_speech_detected(audio_file: Path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "   "}

    transcriber = SpeechTranscriber(model=mock_model)

    with pytest.raises(ValueError, match="No speech was detected"):
        transcriber.transcribe(audio_file)
