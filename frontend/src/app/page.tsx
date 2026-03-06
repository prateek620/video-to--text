"use client";

import { useMemo, useState } from "react";

const DEFAULT_FORMAT = "markdown";

const formatOptions = [
  { value: "markdown", label: "Markdown" },
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "DOCX" },
];

export default function Home() {
  const [selectedVideoFiles, setSelectedVideoFiles] = useState<FileList | null>(null);
  const [link, setLink] = useState("");
  const [mergeUploads, setMergeUploads] = useState(false);
  const [mergeLinks, setMergeLinks] = useState(false);
  const [uploadFormat, setUploadFormat] = useState(DEFAULT_FORMAT);
  const [linkFormat, setLinkFormat] = useState(DEFAULT_FORMAT);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingDetail, setProcessingDetail] = useState<string | null>(null);

  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    []
  );

  const handleUpload = async () => {
    if (!selectedVideoFiles || selectedVideoFiles.length === 0) {
      setError("Please select at least one video file to upload.");
      return;
    }

    setError(null);
    setUploadProgress(0);
    setStatus("Uploading...");

    const formData = new FormData();
    Array.from(selectedVideoFiles).forEach((file) => formData.append("files", file));

    const request = new XMLHttpRequest();
    request.open(
      "POST",
      `${apiBase}/upload-video?merge_videos=${mergeUploads}&output_format=${uploadFormat}`
    );

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setUploadProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    request.onload = () => {
      if (request.status >= 200 && request.status < 300) {
        const response = JSON.parse(request.responseText) as { job_id: string };
        setJobId(response.job_id);
        setStatus("Processing started.");
      } else {
        setError("Upload failed. Please try again.");
        setStatus(null);
      }
    };

    request.onerror = () => {
      setError("Upload failed. Please check your connection.");
      setStatus(null);
    };

    request.send(formData);
  };

  const handleLink = async () => {
    if (!link.trim()) {
      setError("Please enter a video or playlist URL.");
      return;
    }

    setError(null);
    setStatus("Submitting link...");

    const response = await fetch(`${apiBase}/upload-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: link.trim(),
        merge_videos: mergeLinks,
        output_format: linkFormat,
      }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      setError(payload.detail || "Failed to submit link.");
      setStatus(null);
      return;
    }

    const payload = (await response.json()) as { job_id: string };
    setJobId(payload.job_id);
    setStatus("Processing started.");
  };

  const refreshStatus = async () => {
    if (!jobId) {
      setError("Provide a job id to check status.");
      return;
    }

    setError(null);
    const response = await fetch(`${apiBase}/processing-status?job_id=${jobId}`);
    if (!response.ok) {
      setError("Unable to fetch status.");
      return;
    }

    const payload = (await response.json()) as {
      status: string;
      progress: number;
      detail?: string;
    };
    setStatus(`Status: ${payload.status}`);
    setProcessingDetail(payload.detail || null);
    setUploadProgress(Math.min(100, Math.round(payload.progress * 100)));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-12">
        <header className="space-y-4">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">
            Video2Knowledge AI
          </p>
          <h1 className="text-3xl font-semibold md:text-4xl">
            Turn long videos into structured knowledge documents.
          </h1>
          <p className="max-w-2xl text-slate-300">
            Upload videos, paste playlist links, and generate documentation-style
            outputs with chapters, timestamps, and semantic search support.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
            <h2 className="text-xl font-semibold">Direct Upload</h2>
            <p className="mt-2 text-sm text-slate-400">
              Upload multiple videos and optionally merge them into one knowledge
              document.
            </p>
            <div className="mt-4 space-y-4">
              <input
                type="file"
                multiple
                onChange={(event) => setSelectedVideoFiles(event.target.files)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm"
              />
              <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={mergeUploads}
                    onChange={(event) => setMergeUploads(event.target.checked)}
                  />
                  Merge uploads into one document
                </label>
                <select
                  value={uploadFormat}
                  onChange={(event) => setUploadFormat(event.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                >
                  {formatOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleUpload}
                className="w-full rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-400"
              >
                Start Upload
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
            <h2 className="text-xl font-semibold">Video or Playlist Link</h2>
            <p className="mt-2 text-sm text-slate-400">
              Paste links from YouTube, Vimeo, Dailymotion, Google Drive, or
              Dropbox.
            </p>
            <div className="mt-4 space-y-4">
              <input
                value={link}
                onChange={(event) => setLink(event.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm"
              />
              <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={mergeLinks}
                    onChange={(event) => setMergeLinks(event.target.checked)}
                  />
                  Merge playlist videos
                </label>
                <select
                  value={linkFormat}
                  onChange={(event) => setLinkFormat(event.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                >
                  {formatOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleLink}
                className="w-full rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-400"
              >
                Submit Link
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
          <h2 className="text-xl font-semibold">Processing Status</h2>
          <p className="mt-2 text-sm text-slate-400">
            Track background processing and refresh the job status.
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
            <div className="space-y-2">
              <p className="text-sm text-slate-300">
                Job ID: <span className="font-mono">{jobId || "—"}</span>
              </p>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-indigo-400 transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-slate-300">{status || "Idle"}</p>
              {processingDetail ? (
                <p className="text-xs text-slate-500">{processingDetail}</p>
              ) : null}
            </div>
            <button
              onClick={refreshStatus}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:border-slate-500"
            >
              Refresh Status
            </button>
          </div>
          {error ? (
            <p className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
              {error}
            </p>
          ) : null}
        </section>
      </main>
    </div>
  );
}
