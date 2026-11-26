# GTA 6 Mobile Clipper — starter project

A mobile-friendly Flask web app that accepts an authorized video upload and creates multiple MP4 clips.

## Important limitations
- This is a working starter, not a finished AI highlight detector.
- It samples clip start points evenly across the uploaded video.
- It does not download YouTube streams or bypass age gates, logins, DRM, or platform restrictions.
- Vertical output uses a center crop, not AI subject tracking.
- Hosting providers may impose upload, runtime, storage and bandwidth limits.

## Run locally
Requires Python 3.11+ and FFmpeg installed.

```bash
pip install -r requirements.txt
python app.py
```
Open `http://localhost:8000`.

## Deploy
Deploy this folder to a Docker-capable host. The included Dockerfile installs FFmpeg.
Set a strong `SECRET_KEY`. Add authentication, persistent storage, file expiry, rate limits and a background job queue before public use.

Only upload videos you own or have permission to edit. Follow copyright law and the source platform's terms.
