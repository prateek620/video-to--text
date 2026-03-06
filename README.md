# Video2Knowledge AI

Video2Knowledge AI converts long-form videos into structured, technical knowledge documents. Users can upload videos or submit links, and the system generates a documentation-style report with chapters, key insights, and timestamped references.

## System Architecture

1. **Ingestion**: Accepts direct uploads, video links, playlist URLs, or multiple videos for merging.
2. **Downloader**: Detects platform and downloads content with `yt-dlp`.
3. **Audio Processing**: Extracts audio via FFmpeg.
4. **Speech-to-Text**: Generates timestamped transcripts (Whisper/WhisperX ready).
5. **Frame Analysis**: Extracts frames and detects scene changes.
6. **OCR + Visual Understanding**: Reads slide text and generates frame descriptions.
7. **Multimodal Fusion**: Combines speech, OCR, and visual context.
8. **Knowledge Builder**: Filters filler, segments topics, builds chapters, and extracts insights.
9. **Document Generator**: Outputs Markdown, PDF, and DOCX files.
10. **Indexing**: Builds embeddings for semantic search and knowledge graph extraction.

## Backend Folder Structure

```
backend/
  app/
    api/                 # FastAPI routes
    core/                # Settings and config
    schemas/             # API request/response models
    services/            # Pipeline services
    tasks/               # Celery/Redis integration
    storage/             # Local storage (uploads, docs, audio, frames)
```

## API Endpoints

- `POST /upload-video` – Upload one or more videos
- `POST /upload-link` – Submit a video/playlist URL
- `GET /processing-status` – Check job status
- `GET /download-document` – Download Markdown/PDF/DOCX output
- `GET /search-knowledge` – Semantic search over generated knowledge

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Environment variables are read from `.env` with prefix `V2K_`. Set `V2K_ALLOW_VIDEO_DOWNLOADS=true` to enable `yt-dlp` downloads.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI is available at `http://localhost:3000` and communicates with the FastAPI backend on port `8000`.
