# Flask layer: upload handling, job status, and user-facing errors.
# Transcription itself lives in AudioFileLoader / SpeechTranscriber /
# TimestampedTranscriber.

import copy
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock, RLock
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from audio_loader import AudioFileLoader
from timestamped_transcriber import TimestampedTranscriber

BASE_DIR = Path(__file__).resolve().parent
# Local overrides live in .env.loc (create from env.example).
load_dotenv(BASE_DIR / ".env.loc")

UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
ALLOWED = {
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", ".wav,.mp3").split(",")
    if ext.strip()
}
MAX_FILES = int(os.getenv("MAX_FILES", "10"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "100"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_MB * 1024 * 1024
UPLOAD_DIR.mkdir(exist_ok=True)

# One shared Whisper model. RLock so get_transcriber() can run while
# transcribe_one() already holds the lock.
transcriber = None
model_lock = RLock()

# In-memory job store. Fine for a local demo; jobs disappear on restart.
jobs = {}
jobs_lock = Lock()
pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def get_transcriber():
    """Load Whisper once and reuse it for later requests."""
    global transcriber
    with model_lock:
        if transcriber is None:
            transcriber = TimestampedTranscriber(model_name=WHISPER_MODEL)
        return transcriber


def friendly_error(err):
    """Map internal exceptions to messages safe to show in the UI."""
    msg = str(err).lower()
    if isinstance(err, FileNotFoundError):
        return "Audio file could not be found."
    if "unsupported" in msg:
        return "Unsupported audio format. Please upload a WAV or MP3 file."
    if "empty" in msg:
        return "Audio file is empty."
    if "no speech" in msg:
        return "No speech was detected in the audio file."
    return "Transcription failed. Please try again."


def update_file(job_id, file_id, **changes):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return
        for item in job["files"]:
            if item["id"] == file_id:
                item.update(changes)
                break
        finished = all(item["status"] in ("completed", "failed") for item in job["files"])
        job["status"] = "completed" if finished else "processing"


def transcribe_one(job_id, file_id, path):
    """Background worker for a single uploaded file."""
    update_file(job_id, file_id, status="processing")
    try:
        audio = AudioFileLoader(path).load_audio_file()

        # Whisper's Python API is not thread-safe; run one file at a time.
        with model_lock:
            segments = get_transcriber().transcribe_with_timestamps(audio)

        text = " ".join(seg["text"] for seg in segments if seg["text"]).strip()
        if not text:
            raise ValueError("No speech was detected in the audio file")

        stamped = [
            {
                "start": TimestampedTranscriber.format_time(seg["start"]),
                "end": TimestampedTranscriber.format_time(seg["end"]),
                "text": seg["text"],
            }
            for seg in segments
        ]
        update_file(job_id, file_id, status="completed", full_text=text, segments=stamped)
    except Exception as e:
        update_file(job_id, file_id, status="failed", error=friendly_error(e))
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def get_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return None
        # Copy so the UI/API can read while a worker is still updating.
        snapshot = copy.deepcopy(job)

    # Don't send local filesystem paths to the browser.
    for item in snapshot["files"]:
        item.pop("path", None)
    return snapshot


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    files = [f for f in request.files.getlist("audio_files") if f and f.filename]
    if not files:
        flash("Please select an audio file.")
        return redirect(url_for("index"))
    if len(files) > MAX_FILES:
        flash(f"Please upload at most {MAX_FILES} files at a time.")
        return redirect(url_for("index"))

    job_id = uuid4().hex
    items = []

    for uploaded in files:
        name = secure_filename(uploaded.filename)
        ext = Path(name).suffix.lower()
        if not name or ext not in ALLOWED:
            flash("Unsupported audio format. Please upload a WAV or MP3 file.")
            return redirect(url_for("index"))

        # Ignore the original filename; store under a unique name on disk.
        dest = UPLOAD_DIR / f"{uuid4().hex}{ext}"
        uploaded.save(dest)
        if dest.stat().st_size == 0:
            dest.unlink()
            flash("Audio file is empty.")
            return redirect(url_for("index"))

        items.append({
            "id": uuid4().hex,
            "name": name,
            "path": dest,
            "status": "queued",
            "full_text": None,
            "segments": [],
            "error": None,
        })

    with jobs_lock:
        jobs[job_id] = {"id": job_id, "status": "queued", "files": items}

    # Return the status page immediately; workers fill in results later.
    for item in items:
        pool.submit(transcribe_one, job_id, item["id"], item["path"])

    return redirect(url_for("job_page", job_id=job_id))


@app.route("/jobs/<job_id>")
def job_page(job_id):
    job = get_job(job_id)
    if not job:
        flash("Transcription job could not be found.")
        return redirect(url_for("index"))
    return render_template("job.html", job=job)


@app.route("/api/jobs/<job_id>")
def job_api(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.errorhandler(413)
def too_large(_e):
    flash(f"Upload is too large. Maximum total size is {MAX_CONTENT_LENGTH_MB} MB.")
    return redirect(url_for("index")), 413


if __name__ == "__main__":
    # threaded=True lets the job page keep polling while workers run.
    app.run(debug=True, threaded=True)
