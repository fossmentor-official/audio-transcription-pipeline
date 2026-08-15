"""Unit tests for AudioFileLoader."""

from pathlib import Path

import pytest

from audio_loader import AudioFileLoader


@pytest.fixture
def tmp_mp3(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.mp3"
    file_path.write_bytes(b"fake audio bytes")
    return file_path


@pytest.fixture
def tmp_wav(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.wav"
    file_path.write_bytes(b"fake audio bytes")
    return file_path


def test_valid_mp3_is_returned(tmp_mp3: Path):
    result = AudioFileLoader(tmp_mp3).load_audio_file()
    assert result == tmp_mp3


def test_valid_wav_is_returned(tmp_wav: Path):
    result = AudioFileLoader(tmp_wav).load_audio_file()
    assert result == tmp_wav


def test_missing_file_raises(tmp_path: Path):
    missing = tmp_path / "does_not_exist.mp3"
    with pytest.raises(FileNotFoundError):
        AudioFileLoader(missing).load_audio_file()


def test_unsupported_extension_raises(tmp_path: Path):
    bad_file = tmp_path / "sample.txt"
    bad_file.write_text("not audio")
    with pytest.raises(ValueError, match="Unsupported audio format"):
        AudioFileLoader(bad_file).load_audio_file()


def test_empty_file_raises(tmp_path: Path):
    empty_file = tmp_path / "empty.wav"
    empty_file.touch()
    with pytest.raises(ValueError, match="empty"):
        AudioFileLoader(empty_file).load_audio_file()
