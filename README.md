# AI Audio Transcription

A small, interview-focused Flask application that validates an uploaded WAV/MP3 file, transcribes speech with open-source OpenAI Whisper (`openai-whisper`), and returns both full text and per-segment timestamps.

## Architecture

```
Browser
   |
   v
Flask Web Layer (app.py)
   |
   v
AudioFileLoader          -> file validation
   |
   v
TimestampedTranscriber   -> speech-to-text + timestamped segments
   |
   +---- SpeechTranscriber -> speech-to-text
   |
   v
OpenAI Whisper (local model)
   |
   v
Transcription Result
```

## Project structure

```
audio-transcription-pipeline/
├── app.py
├── audio_loader.py
├── speech_transcriber.py
├── timestamped_transcriber.py
├── env.example
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html
│   └── job.html
├── static/
│   └── style.css
├── uploads/
│   └── .gitkeep
└── tests/
    ├── test_audio_loader.py
    ├── test_speech_transcriber.py
    └── test_timestamped_transcriber.py
```

## How the three assignment tasks map to the implementation

**Task 1: AudioFileLoader** (`audio_loader.py`)  
Validates that an audio path exists, has a supported extension (`.wav` / `.mp3`), and is non-empty.

**Task 2: SpeechTranscriber** (`speech_transcriber.py`)  
Reuses `AudioFileLoader` for validation, loads Whisper once per service instance, and returns plain transcription text.

**Task 3: TimestampedTranscriber** (`timestamped_transcriber.py`)  
Extends `SpeechTranscriber` and returns structured segments (`start`, `end`, `text`) plus a readable timestamp formatter.

## Installation

### 1. System dependency: ffmpeg

Whisper requires `ffmpeg` to decode audio.

macOS (Homebrew):

```bash
brew install ffmpeg
```

Ubuntu/Debian:

```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. Python environment and dependencies

Python 3.10+ recommended.

```bash
cd audio-transcription-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to run the application

```bash
source .venv/bin/activate
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000), upload one or more WAV/MP3 files, and click **Transcribe Audio**.

Uploads return immediately to a job page. Transcription continues in background worker threads while the page polls for progress.

The Whisper model is loaded lazily on the first transcription request and reused afterward. The first run may download the model and take longer.

Default model is `tiny` for faster local demos. Switch models in `.env.loc`:

```bash
WHISPER_MODEL=tiny
# or
WHISPER_MODEL=turbo
```

If you do not have a local settings file yet:

```bash
cp env.example .env.loc
```

`env.example` is committed to GitHub. `.env.loc` stays on your machine only (gitignored).

Runtime transcription text and timestamps come from Whisper for the uploaded file. They are not hard-coded.

## How to run tests

```bash
source .venv/bin/activate
pytest -q
```

Unit tests mock Whisper so no model download is required.

## Example workflow

1. Open the upload page.
2. Choose one or more `.wav` / `.mp3` files (up to 10, 100 MB total).
3. Click **Transcribe Audio**.
4. Watch the job page update as each file moves from queued → processing → completed.
5. Review full text and timestamped segments per file.
6. Click **Transcribe Another File** to start over.

## Design decisions

- **Progressive OOP services**: Task 1 validation → Task 2 transcription → Task 3 timestamped inheritance, without duplicating validation.
- **Flask only for UI/API**: Upload handling and error display stay in `app.py`; transcription logic stays in service classes.
- **Async multi-file jobs**: Files are accepted together, processed on a thread pool, and tracked in memory with JSON polling — no Redis/Celery.
- **Serialized Whisper inference**: A lock protects the shared model (Whisper is not safely concurrent); jobs still feel async in the UI.
- **Local Whisper only**: Uses `openai-whisper`, not the hosted OpenAI API.
- **Lazy shared model**: Model initialized once per process and reused across requests.
- **Basic upload safety**: `secure_filename`, unique server-side names, extension allow-list, size limit, uploads ignored by Git.
- **No over-engineering**: No auth, database, external queues, Docker, or cloud storage.
