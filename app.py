import os, uuid, subprocess, shutil
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deploying")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2 GB; hosting limits may be lower
ALLOWED = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def duration_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(out.stdout.strip())

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/create")
def create():
    video = request.files.get("video")
    if not video or not video.filename:
        flash("Choose a video file first.")
        return redirect(url_for("home"))

    ext = Path(video.filename).suffix.lower()
    if ext not in ALLOWED:
        flash("Supported formats: MP4, MOV, MKV, WEBM and M4V.")
        return redirect(url_for("home"))

    try:
        count = max(1, min(35, int(request.form.get("count", 10))))
        clip_len = max(5, min(90, int(request.form.get("clip_len", 20))))
    except ValueError:
        flash("Clip count and duration must be numbers.")
        return redirect(url_for("home"))

    job = uuid.uuid4().hex[:10]
    source = UPLOADS / f"{job}{ext}"
    job_dir = OUTPUTS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    video.save(source)

    try:
        total = duration_of(source)
        if total < clip_len:
            raise ValueError(f"Video is only {total:.1f} seconds long; choose a shorter clip duration.")

        # Spread clips across the source. This is a deterministic starter workflow,
        # not AI highlight detection.
        max_start = max(0, total - clip_len)
        if count == 1:
            starts = [max_start / 2]
        else:
            starts = [max_start * i / (count - 1) for i in range(count)]

        aspect = request.form.get("aspect", "vertical")
        if aspect == "landscape":
            vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
        else:
            # Center-crop to 9:16; can be changed to smart subject tracking later.
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

        made = []
        for i, start in enumerate(starts, 1):
            out = job_dir / f"clip_{i:02d}.mp4"
            run([
                "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source),
                "-t", str(clip_len), "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                str(out)
            ])
            made.append(out.name)

        source.unlink(missing_ok=True)
        return render_template("done.html", job=job, clips=made, count=len(made))
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        source.unlink(missing_ok=True)
        flash(f"Could not process video: {exc}")
        return redirect(url_for("home"))

@app.get("/download/<job>/<filename>")
def download(job, filename):
    folder = OUTPUTS / job
    if not folder.is_dir() or Path(filename).name != filename:
        return "Not found", 404
    return send_from_directory(folder, filename, as_attachment=True)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
