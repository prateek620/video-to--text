"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const DEFAULT_FORMAT = "markdown";

const formatOptions = [
  { value: "markdown", label: "Markdown" },
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "DOCX" },
];

type InputTab = "upload" | "link";

type JobStatus = "idle" | "uploading" | "processing" | "done" | "error";

export default function Home() {
  const [activeTab, setActiveTab] = useState<InputTab>("upload");
  const [selectedVideoFiles, setSelectedVideoFiles] = useState<FileList | null>(null);
  const [link, setLink] = useState("");
  const [mergeUploads, setMergeUploads] = useState(false);
  const [mergeLinks, setMergeLinks] = useState(false);
  const [uploadFormat, setUploadFormat] = useState(DEFAULT_FORMAT);
  const [linkFormat, setLinkFormat] = useState(DEFAULT_FORMAT);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus>("idle");
  const [statusLabel, setStatusLabel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingDetail, setProcessingDetail] = useState<string | null>(null);
  const [availableFormats, setAvailableFormats] = useState<string[]>([]);

  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    []
  );

  const isActive = jobStatus === "uploading" || jobStatus === "processing";

  const fetchStatus = useCallback(async (id: string) => {
    const response = await fetch(`${apiBase}/processing-status?job_id=${id}`);
    if (!response.ok) {
      setError("Unable to fetch status.");
      return;
    }

    const payload = (await response.json()) as {
      status: string;
      progress: number;
      detail?: string;
      output_formats?: string[];
    };

    setStatusLabel(payload.status);
    setProcessingDetail(payload.detail || null);
    setAvailableFormats(payload.output_formats || []);
    setUploadProgress(Math.min(100, Math.round(payload.progress * 100)));

    if (payload.status === "done" || payload.status === "completed") {
      setJobStatus("done");
    } else if (payload.status === "error" || payload.status === "failed") {
      setJobStatus("error");
      setError(payload.detail || "Processing failed.");
    } else {
      setJobStatus("processing");
    }
  }, [apiBase]);

  // Auto-poll every 5 seconds while a job is active
  useEffect(() => {
    if (!jobId || jobStatus !== "processing") return;

    pollTimerRef.current = setTimeout(() => {
      fetchStatus(jobId);
    }, 5000);

    return () => {
      if (pollTimerRef.current !== null) clearTimeout(pollTimerRef.current);
    };
  }, [jobId, jobStatus, fetchStatus]);

  const startJob = (id: string) => {
    setJobId(id);
    setJobStatus("processing");
    setError(null);
    setAvailableFormats([]);
    fetchStatus(id);
  };

  const handleUpload = async () => {
    if (!selectedVideoFiles || selectedVideoFiles.length === 0) {
      setError("Please select at least one video file to upload.");
      return;
    }

    setError(null);
    setUploadProgress(0);
    setStatusLabel("Uploading…");
    setJobStatus("uploading");
    setAvailableFormats([]);

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
        startJob(response.job_id);
      } else {
        setError("Upload failed. Please try again.");
        setJobStatus("error");
      }
    };

    request.onerror = () => {
      setError("Upload failed. Please check your connection.");
      setJobStatus("error");
    };

    request.send(formData);
  };

  const handleLink = async () => {
    if (!link.trim()) {
      setError("Please enter a video or playlist URL.");
      return;
    }

    setError(null);
    setStatusLabel("Submitting link…");
    setJobStatus("uploading");
    setAvailableFormats([]);

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
      setError((payload as { detail?: string }).detail || "Failed to submit link.");
      setJobStatus("error");
      return;
    }

    const payload = (await response.json()) as { job_id: string };
    startJob(payload.job_id);
  };

  const refreshStatus = () => {
    if (!jobId) {
      setError("No active job to refresh.");
      return;
    }
    setError(null);
    fetchStatus(jobId);
  };

  const stepState = (step: number): "done" | "active" | "pending" => {
    if (step === 1) {
      return jobStatus !== "idle" ? "done" : "active";
    }
    if (step === 2) {
      if (jobStatus === "done") return "done";
      if (jobStatus === "processing" || jobStatus === "uploading") return "active";
      return "pending";
    }
    if (step === 3) {
      return jobStatus === "done" ? "active" : "pending";
    }
    return "pending";
  };

  const stepClass = (state: "done" | "active" | "pending") => {
    if (state === "done") return "bg-emerald-500 text-white";
    if (state === "active") return "bg-indigo-500 text-white";
    return "bg-slate-700 text-slate-400";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-12">
        {/* Header */}
        <header className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
            Video2Knowledge AI
          </p>
          <h1 className="text-3xl font-semibold md:text-4xl">
            Turn long videos into structured knowledge documents.
          </h1>
          <p className="text-slate-400 text-sm">
            Upload a video file or paste a link to generate documentation-style
            outputs with chapters, timestamps, and semantic search support.
          </p>
        </header>

        {/* Step indicators */}
        <ol className="flex items-center gap-0">
          {[
            { n: 1, label: "Choose input" },
            { n: 2, label: "Processing" },
            { n: 3, label: "Download" },
          ].map(({ n, label }, idx) => {
            const state = stepState(n);
            return (
              <li key={n} className="flex flex-1 items-center">
                <div className="flex flex-col items-center gap-1">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${stepClass(state)}`}
                  >
                    {state === "done" ? "✓" : n}
                  </span>
                  <span className="text-xs text-slate-400 whitespace-nowrap">{label}</span>
                </div>
                {idx < 2 && (
                  <div className="mx-2 h-px flex-1 bg-slate-700" />
                )}
              </li>
            );
          })}
        </ol>

        {/* Step 1: Input */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg space-y-5">
          <h2 className="text-lg font-semibold">Step 1 — Choose your input</h2>

          {/* Tabs */}
          <div className="flex gap-1 rounded-lg border border-slate-700 bg-slate-950 p-1 w-fit">
            <button
              onClick={() => setActiveTab("upload")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
                activeTab === "upload"
                  ? "bg-indigo-500 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Upload File
            </button>
            <button
              onClick={() => setActiveTab("link")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
                activeTab === "link"
                  ? "bg-indigo-500 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Paste Link
            </button>
          </div>

          {activeTab === "upload" && (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Upload one or more video files. Optionally merge them into a single document.
              </p>
              <input
                type="file"
                multiple
                accept="video/*"
                onChange={(event) => setSelectedVideoFiles(event.target.files)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm"
              />
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={mergeUploads}
                    onChange={(event) => setMergeUploads(event.target.checked)}
                  />
                  Merge into one document
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Format:</span>
                  <select
                    value={uploadFormat}
                    onChange={(event) => setUploadFormat(event.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
                  >
                    {formatOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                onClick={handleUpload}
                disabled={isActive}
                className="w-full rounded-lg bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isActive ? "Processing…" : "Start Upload"}
              </button>
            </div>
          )}

          {activeTab === "link" && (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Paste a link from YouTube, Vimeo, Dailymotion, Google Drive, or Dropbox.
              </p>
              {/* YouTube info note */}
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-200 space-y-1">
                <p className="font-semibold">YouTube / external downloads</p>
                <p>
                  Video downloads must be enabled in the backend. Set{" "}
                  <code className="rounded bg-amber-500/20 px-1 py-0.5 font-mono">
                    V2K_ALLOW_VIDEO_DOWNLOADS=true
                  </code>{" "}
                  in your backend <code className="font-mono">.env</code> file, then restart the server.
                </p>
              </div>
              <input
                value={link}
                onChange={(event) => setLink(event.target.value)}
                placeholder="https://www.youtube.com/watch?v=…"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm"
              />
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={mergeLinks}
                    onChange={(event) => setMergeLinks(event.target.checked)}
                  />
                  Merge playlist videos
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Format:</span>
                  <select
                    value={linkFormat}
                    onChange={(event) => setLinkFormat(event.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
                  >
                    {formatOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                onClick={handleLink}
                disabled={isActive}
                className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isActive ? "Processing…" : "Submit Link"}
              </button>
            </div>
          )}
        </section>

        {/* Step 2: Processing status */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Step 2 — Processing status</h2>
            <button
              onClick={refreshStatus}
              disabled={!jobId}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Refresh
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Job ID:</span>
              <span className="font-mono text-slate-300">{jobId || "—"}</span>
            </div>

            {/* Progress bar */}
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                <span>{statusLabel || "Waiting for input…"}</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full rounded-full transition-all ${
                    jobStatus === "done" ? "bg-emerald-400" : "bg-indigo-400"
                  }`}
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>

            {/* Spinner while processing */}
            {isActive && (
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <svg
                  className="h-4 w-4 animate-spin text-indigo-400"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                  />
                </svg>
                Auto-refreshing every 5 seconds…
              </div>
            )}

            {processingDetail && (
              <p className="text-xs text-slate-500">{processingDetail}</p>
            )}

            {/* Success state */}
            {jobStatus === "done" && (
              <p className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-200">
                ✓ Processing complete! Your documents are ready to download below.
              </p>
            )}
          </div>

          {error && (
            <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
              {error}
            </p>
          )}
        </section>

        {/* Step 3: Download */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg space-y-4">
          <h2 className="text-lg font-semibold">Step 3 — Download your document</h2>

          {availableFormats.length > 0 && jobId ? (
            <div className="space-y-3">
              <p className="text-sm text-slate-400">
                Your knowledge document is available in the following formats:
              </p>
              <div className="flex flex-wrap gap-3">
                {availableFormats.map((format) => (
                  <a
                    key={format}
                    href={`${apiBase}/download-document?job_id=${jobId}&output_format=${format}`}
                    className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-5 py-2 text-sm font-semibold uppercase text-indigo-300 hover:bg-indigo-500/20 transition"
                  >
                    ↓ {format}
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Download links will appear here once processing is complete.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
