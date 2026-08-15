# AI Audio Transcription

A small Flask application that accepts WAV/MP3 uploads, transcribes speech with local OpenAI Whisper (`openai-whisper`), and returns full text plus per-segment timestamps.

Built as a focused interview assignment: clear OOP services, a thin web layer, and no unnecessary infrastructure.

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

## How the three assignment tasks map to the implementation

**Task 1: AudioFileLoader** (`audio_loader.py`)  
Validates that an audio path exists, has a supported extension (`.wav` / `.mp3`), and is non-empty.

**Task 2: SpeechTranscriber** (`speech_transcriber.py`)  
Reuses `AudioFileLoader` for validation, loads Whisper once per service instance, and returns plain transcription text.

**Task 3: TimestampedTranscriber** (`timestamped_transcriber.py`)  
Extends `SpeechTranscriber` and returns structured segments (`start`, `end`, `text`) plus a readable timestamp formatter.

## Design decisions

### Progressive OOP (Task 1 → 2 → 3)

**Decision:** Keep three separate services and let Task 3 inherit from Task 2.

**Why:** Matches the assignment’s progressive structure and avoids duplicating file-validation logic.

**Tradeoff:** Slightly more files than a single script, but ownership of each responsibility is clear.

### Local Whisper, not the hosted OpenAI API

**Decision:** Use the open-source `openai-whisper` library only.

**Why:** The assignment requires local Whisper and forbids the hosted API.

**Tradeoff:** First run may download a model; CPU inference is slower than a cloud API or GPU.

### Flask is HTTP glue only

**Decision:** Put upload, flash errors, and job status in `app.py`; keep transcription in service classes.

**Why:** Services stay unit-testable without Flask. Templates stay free of business logic.

**Tradeoff:** More layers than “everything in one route,” which is intentional for interview clarity.

### Async multi-file jobs without Celery/Redis

**Decision:** In-memory job store, a small thread pool, and JSON polling from the job page.

**Why:** The UI can return immediately and show `queued` → `processing` → `completed` without external queues.

**Tradeoff:** Jobs disappear on process restart. Acceptable for a local demo; not a production worker system.

### Shared model with a lock

**Decision:** Load Whisper once per process and protect `transcribe` with an `RLock`.

**Why:** Reusing the model avoids reload cost. Whisper’s Python API is not safely concurrent.

**Tradeoff:** Inference is effectively one file at a time under the lock; the UI still updates live per file.

### Config via `env.example` / `.env.loc`

**Decision:** Runtime settings (model name, upload limits, secret key) live in env files, not hard-coded in `app.py`.

**Why:** Easy to switch `tiny` (faster demo) vs `turbo` (higher quality). Local secrets stay off GitHub.

**Tradeoff:** After clone, run `cp env.example .env.loc` before starting the app.

### What we deliberately skipped

No database, auth, Docker, Redis, Celery, or cloud storage.

**Why:** The assignment asked for a simple, locally runnable solution that demonstrates the three transcription capabilities clearly.

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
cp env.example .env.loc
```

`env.example` is committed. `.env.loc` is gitignored and used for local overrides.

## How to run the application

```bash
source .venv/bin/activate
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000), upload one or more WAV/MP3 files, and click **Transcribe Audio**.

Uploads return immediately to a job page. Workers fill in results while the page polls for progress.

The Whisper model is loaded lazily on the first transcription request and reused afterward. The first run may download the model and take longer.

Default model is `tiny` for faster local demos. Switch in `.env.loc`:

```bash
WHISPER_MODEL=tiny
# or
WHISPER_MODEL=turbo
```

Runtime transcription text and timestamps come from Whisper for the uploaded file. They are not hard-coded.

## How to run tests

```bash
source .venv/bin/activate
pytest -q
```

Unit tests mock Whisper so no model download is required.

## Example workflow

1. Open the upload page.
2. Choose one or more `.wav` / `.mp3` files (up to 10, 100 MB total by default).
3. Click **Transcribe Audio**.
4. Watch each file move from `queued` → `processing` → `completed`.
5. Review full text and timestamped segments per file.
6. Click **Transcribe Another File** to start over.
