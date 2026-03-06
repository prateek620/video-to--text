# Video2Knowledge AI

Video2Knowledge AI converts long-form videos into structured, technical knowledge documents. Upload a video file or paste a link and the system generates a documentation-style report with chapters, key insights, and timestamped references.

## Prerequisites

Before you begin, make sure the following are installed on your machine:

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.10+ | Required for the backend |
| Node.js | 18+ | Required for the frontend |
| FFmpeg | Latest | System-level install – used for audio extraction |
| Tesseract OCR | Latest | System-level install – used for slide/frame text recognition |

### Installing system dependencies

**macOS (Homebrew)**
```bash
brew install ffmpeg tesseract
```

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install -y ffmpeg tesseract-ocr
```

**Windows**
Download and install from the official sites:
- FFmpeg: https://ffmpeg.org/download.html
- Tesseract: https://github.com/tesseract-ocr/tesseract

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/prateek620/video-to--text.git
cd video-to--text
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

The default `.env.example` already sets `V2K_ALLOW_VIDEO_DOWNLOADS=true`. Edit the file if you need to change any values.

Start the backend server:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.

### 3. Frontend setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The UI is available at `http://localhost:3000`.

## Environment Variables

All backend settings are read from `backend/.env` using the `V2K_` prefix.

| Variable | Default | Description |
|---|---|---|
| `V2K_ALLOW_VIDEO_DOWNLOADS` | `true` | Enable `yt-dlp` downloads from YouTube and other platforms |
| `V2K_BASE_URL` | `http://localhost:8000` | Public URL of the backend (used for generated links) |

## System Architecture

1. **Ingestion** – Accepts direct uploads, video links, playlist URLs, or multiple videos for merging.
2. **Downloader** – Detects platform and downloads content with `yt-dlp`.
3. **Audio Processing** – Extracts audio via FFmpeg.
4. **Speech-to-Text** – Generates timestamped transcripts using OpenAI Whisper.
5. **Frame Analysis** – Extracts frames and detects scene changes with OpenCV.
6. **OCR + Visual Understanding** – Reads slide text with Tesseract and generates frame descriptions.
7. **Multimodal Fusion** – Combines speech, OCR, and visual context.
8. **Knowledge Builder** – Filters filler, segments topics, builds chapters, and extracts insights.
9. **Document Generator** – Outputs Markdown, PDF, and DOCX files.
10. **Indexing** – Builds embeddings for semantic search using `sentence-transformers` + FAISS.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-video` | Upload one or more video files |
| `POST` | `/upload-link` | Submit a video or playlist URL |
| `GET` | `/processing-status` | Check processing status for a job |
| `GET` | `/download-document` | Download the generated document (Markdown / PDF / DOCX) |
| `GET` | `/search-knowledge` | Semantic search over generated knowledge |

## Backend Folder Structure

```
backend/
  app/
    api/        # FastAPI routes
    core/       # Settings and config
    schemas/    # API request/response models
    services/   # Pipeline services
    tasks/      # Background task integration
    storage/    # Local storage (uploads, docs, audio, frames)
```

## Troubleshooting

### "Video downloads are disabled"

**Error message**: `Video downloads are disabled. Set V2K_ALLOW_VIDEO_DOWNLOADS to a truthy value to enable downloads.`

**Fix**: Open `backend/.env` and set:
```
V2K_ALLOW_VIDEO_DOWNLOADS=true
```
Then restart the backend server. If you don't have a `.env` file yet, copy the example:
```bash
cp backend/.env.example backend/.env
```

### FFmpeg not found

Make sure FFmpeg is installed and available on your `PATH`:
```bash
ffmpeg -version
```
If the command is not found, follow the install instructions in the [Prerequisites](#prerequisites) section.

### Tesseract not found

Make sure Tesseract is installed and on your `PATH`:
```bash
tesseract --version
```
If the command is not found, follow the install instructions in the [Prerequisites](#prerequisites) section.

