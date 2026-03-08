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
 const [selectedVideoFiles, setSelectedVideoFiles] = useState<File[]>([]);
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

  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000", []);
  const isActive = jobStatus === "uploading" || jobStatus === "processing";

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const fetchStatus = useCallback(
    async (id: string) => {
      try {
        const response = await fetch(`${apiBase}/processing-status?job_id=${id}`, { cache: "no-store" });
        if (!response.ok) {
          setError("Unable to fetch status.");
          setJobStatus("error");
          stopPolling();
          return;
        }

        const payload = (await response.json()) as {
          status: string;
          progress: number;
          detail?: string;
          output_formats?: string[];
        };

        const backendStatus = (payload.status || "").toLowerCase();
        setStatusLabel(payload.status || null);
        setProcessingDetail(payload.detail || null);
        setAvailableFormats(payload.output_formats || []);
        setUploadProgress(Math.min(100, Math.max(0, Math.round((payload.progress ?? 0) * 100))));

        if (backendStatus === "completed" || backendStatus === "done") {
          setJobStatus("done");
          setStatusLabel("completed");
          stopPolling();
          return;
        }

        if (backendStatus === "failed" || backendStatus === "error") {
          setJobStatus("error");
          setError(payload.detail || "Processing failed.");
          stopPolling();
          return;
        }

        setJobStatus("processing");
      } catch (e) {
        setJobStatus("error");
        setError(e instanceof Error ? e.message : "Status check failed");
        stopPolling();
      }
    },
    [apiBase]
  );

  useEffect(() => {
    stopPolling();
    if (!jobId) return;
    if (jobStatus === "done" || jobStatus === "error") return;
    pollTimerRef.current = setTimeout(() => fetchStatus(jobId), 3000);
    return stopPolling;
  }, [jobId, jobStatus, fetchStatus]);

  const startJob = (id: string) => {
    setJobId(id);
    setJobStatus("processing");
    setError(null);
    setAvailableFormats([]);
    setStatusLabel("processing");
    setProcessingDetail("Job accepted");
    setUploadProgress(1);
    fetchStatus(id);
  };

  const handleUpload = () => {
    if (!selectedVideoFiles.length) {
      setError("Please select at least one video file to upload.");
      return;
    }

    setError(null);
    setUploadProgress(0);
    setStatusLabel("Uploading…");
    setProcessingDetail("Uploading files");
    setJobStatus("uploading");
    setAvailableFormats([]);

    const formData = new FormData();
    selectedVideoFiles.forEach((file) => formData.append("files", file));

    const request = new XMLHttpRequest();
    request.open("POST", `${apiBase}/upload-video?merge_videos=${mergeUploads}&output_format=${uploadFormat}`);

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) setUploadProgress(Math.max(1, Math.round((event.loaded / event.total) * 100)));
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

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files ? Array.from(event.target.files) : [];
    setSelectedVideoFiles(files);
  };

  const handleLink = async () => {
    if (!link.trim()) {
      setError("Please enter a video or playlist URL.");
      return;
    }
    setError(null);
    setStatusLabel("Submitting link…");
    setProcessingDetail("Submitting link");
    setUploadProgress(1);
    setJobStatus("uploading");
    setAvailableFormats([]);
    try {
      const response = await fetch(`${apiBase}/upload-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: link.trim(), merge_videos: mergeLinks, output_format: linkFormat }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        setError((payload as { detail?: string }).detail || "Failed to submit link.");
        setJobStatus("error");
        return;
      }

      const payload = (await response.json()) as { job_id: string };
      startJob(payload.job_id);
    } catch (error) {
      setError(error instanceof Error ? `Failed to submit link. ${error.message}` : "Failed to submit link.");
      setJobStatus("error");
    }
  };

  const refreshStatus = () => {
    if (!jobId) return;
    fetchStatus(jobId);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Video2Knowledge AI</p>
          <h1 className="text-3xl font-semibold md:text-4xl">Turn long videos into structured knowledge documents.</h1>
        </header>

        {/* Step 1: Input */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-5">
          <h2 className="text-lg font-semibold">Step 1 — Choose your input</h2>

          <div className="flex gap-1 rounded-lg border border-slate-700 bg-slate-950 p-1 w-fit">
            <button onClick={() => setActiveTab("upload")} className={`rounded-md px-4 py-1.5 text-sm ${activeTab === "upload" ? "bg-indigo-500 text-white" : "text-slate-400"}`}>Upload File</button>
            <button onClick={() => setActiveTab("link")} className={`rounded-md px-4 py-1.5 text-sm ${activeTab === "link" ? "bg-indigo-500 text-white" : "text-slate-400"}`}>Paste Link</button>
          </div>

          {activeTab === "upload" ? (
            <div className="space-y-4">
              <input
  type="file"
  multiple
  accept="video/*"
  onChange={e => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    setSelectedVideoFiles(files);
  }}
  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm"
/>
              <div className="flex items-center gap-4 text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={mergeUploads} onChange={(e) => setMergeUploads(e.target.checked)} />
                  Merge into one document
                </label>
                <select value={uploadFormat} onChange={(e) => setUploadFormat(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm">
                  {formatOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <button onClick={handleUpload} disabled={isActive} className="w-full rounded-lg bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
                {isActive ? "Processing…" : "Start Upload"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://www.youtube.com/watch?v=…" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm" />
              <div className="flex items-center gap-4 text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={mergeLinks} onChange={(e) => setMergeLinks(e.target.checked)} />
                  Merge playlist videos
                </label>
                <select value={linkFormat} onChange={(e) => setLinkFormat(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm">
                  {formatOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <button onClick={handleLink} disabled={isActive} className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
                {isActive ? "Processing…" : "Submit Link"}
              </button>
            </div>
          )}
        </section>

        {/* Step 2: Processing status */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Step 2 — Processing status</h2>
            <button onClick={refreshStatus} disabled={!jobId} className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs">Refresh</button>
          </div>
          <p className="text-sm text-slate-400">Job ID: <span className="font-mono text-slate-300">{jobId || "—"}</span></p>
          <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
            <span>{statusLabel || "Waiting for input…"}</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
            <div className={`h-full rounded-full transition-all ${jobStatus === "done" ? "bg-emerald-400" : "bg-indigo-400"}`} style={{ width: `${uploadProgress}%` }} />
          </div>
          {processingDetail && <p className="text-xs text-slate-500">{processingDetail}</p>}
          {jobStatus === "done" && <p className="text-sm text-emerald-300">✓ Processing complete</p>}
          {error && <p className="text-sm text-red-300">{error}</p>}
        </section>

        {/* Step 3: Download */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <h2 className="text-lg font-semibold">Step 3 — Download your document</h2>
          {availableFormats.length > 0 && jobId ? (
            <div className="flex flex-wrap gap-3">
              {availableFormats.map((format) => (
                <a key={format} href={`${apiBase}/download-document?job_id=${jobId}&output_format=${format}`} className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-5 py-2 text-sm font-semibold uppercase text-indigo-300">
                  ↓ {format}
                </a>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Download links will appear here once processing is complete.</p>
          )}
        </section>
      </main>
    </div>
  );
}