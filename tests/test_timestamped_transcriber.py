"""Unit tests for TimestampedTranscriber with mocked Whisper."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from timestamped_transcriber import TimestampedTranscriber


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "speech.wav"
    path.write_bytes(b"fake audio")
    return path


def test_timestamped_segments_returned(audio_file: Path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 2.84, "text": " Hello"},
            {"start": 2.84, "end": 6.12, "text": " world"},
        ]
    }

    transcriber = TimestampedTranscriber(model=mock_model)
    segments = transcriber.transcribe_with_timestamps(audio_file)

    assert segments == [
        {"start": 0.0, "end": 2.84, "text": "Hello"},
        {"start": 2.84, "end": 6.12, "text": "world"},
    ]


def test_no_segments_detected(audio_file: Path):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": []}

    transcriber = TimestampedTranscriber(model=mock_model)

    with pytest.raises(ValueError, match="No speech segments"):
        transcriber.transcribe_with_timestamps(audio_file)


def test_format_time():
    assert TimestampedTranscriber.format_time(0) == "00:00.00"
    assert TimestampedTranscriber.format_time(2.84) == "00:02.84"
    assert TimestampedTranscriber.format_time(125.5) == "02:05.50"
