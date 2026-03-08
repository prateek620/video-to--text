"use client";

import { useEffect, useState } from "react";

const DEFAULT_FORMAT = "markdown";

const formatOptions = [
  { value: "markdown", label: "Markdown" },
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "DOCX" },
];

type InputTab = "upload" | "link";
type JobStatus = "idle" | "queued" | "uploading" | "processing" | "done" | "error" | "failed";

export default function Home() {
  const [activeTab, setActiveTab] = useState<InputTab>("upload");
  const [jobId, setJobId] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<JobStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [detail, setDetail] = useState("");
  const [outputFormats, setOutputFormats] = useState<string[]>([]);
  const [link, setLink] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  // Poll for status updates
  useEffect(() => {
    if (!jobId) return;
    
    // Stop polling if done or failed
    if (jobStatus === "done" || jobStatus === "failed" || jobStatus === "error") {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/processing-status?job_id=${jobId}`);
        if (!response.ok) {
          console.error("Status check failed");
          return;
        }

        const data = await response.json();
        console.log("Status update:", data); // Debug log
        
        setJobStatus(data.status as JobStatus);
        setProgress(Math.round(data.progress * 100));
        setDetail(data.detail || "");
        if (data.output_formats) {
          setOutputFormats(data.output_formats);
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 1000); // Poll every 1 second

    return () => clearInterval(pollInterval);
  }, [jobId]); // Remove jobStatus from dependencies to keep polling active

  const handleUploadClick = async () => {
    if (selectedFiles.length === 0) {
      alert("Please select files");
      return;
    }

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    const params = new URLSearchParams({
      merge_videos: "false",
      output_format: DEFAULT_FORMAT,
    });

    try {
      const response = await fetch(`/api/upload-video?${params}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus("uploading");
      setProgress(0);
    } catch (error) {
      console.error("Upload error:", error);
      setJobStatus("error");
      setDetail("Upload failed");
    }
  };

  const handlePasteLink = async () => {
    if (!link) {
      alert("Please paste a link");
      return;
    }

    const params = new URLSearchParams({
      merge_videos: "false",
      output_format: DEFAULT_FORMAT,
    });

    try {
      const response = await fetch(`/api/upload-link?${params}`, {
        method: "POST",
        body: JSON.stringify({ url: link }),
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error("Link upload failed");
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus("processing");
      setProgress(5);
    } catch (error) {
      console.error("Link upload error:", error);
      setJobStatus("error");
      setDetail("Link upload failed");
    }
  };

  const handleRefresh = () => {
    if (jobId) {
      // Manually trigger a status check
      fetch(`/api/processing-status?job_id=${jobId}`)
        .then((res) => res.json())
        .then((data) => {
          setJobStatus(data.status);
          setProgress(Math.round(data.progress * 100));
          setDetail(data.detail || "");
          if (data.output_formats) {
            setOutputFormats(data.output_formats);
          }
        })
        .catch((error) => console.error("Refresh error:", error));
    }
  };

  const handleDownload = (format: string) => {
    if (jobId) {
      window.location.href = `/api/download-document?job_id=${jobId}&format=${format}`;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Step 1 */}
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Step 1 — Choose your input</h2>

          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setActiveTab("upload")}
              className={`px-6 py-2 rounded-lg font-medium transition ${
                activeTab === "upload"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Upload File
            </button>
            <button
              onClick={() => setActiveTab("link")}
              className={`px-6 py-2 rounded-lg font-medium transition ${
                activeTab === "link"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Paste Link
            </button>
          </div>

          {activeTab === "upload" ? (
            <div className="space-y-4">
              <input
                type="file"
                multiple
                accept="video/*"
                onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300"
              />
              <button
                onClick={handleUploadClick}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition"
              >
                Start Upload
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                value={link}
                onChange={(e) => setLink(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=…"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300"
              />
              <button
                onClick={handlePasteLink}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition"
              >
                Process Link
              </button>
            </div>
          )}
        </div>

        {/* Step 2 */}
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Step 2 — Processing status</h2>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition"
            >
              Refresh
            </button>
          </div>

          {jobId && (
            <div className="space-y-4">
              <div className="text-sm text-slate-400">Job ID: {jobId}</div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">{jobStatus}</span>
                <span className="text-sm text-slate-400">{progress}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              {detail && <div className="text-sm text-slate-400">{detail}</div>}
            </div>
          )}
        </div>

        {/* Step 3 */}
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Step 3 — Download your document</h2>

          {jobStatus === "done" && outputFormats.length > 0 ? (
            <div className="flex flex-wrap gap-3">
              {outputFormats.map((format) => (
                <button
                  key={format}
                  onClick={() => handleDownload(format)}
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition"
                >
                  Download {format.toUpperCase()}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">Download links will appear here once processing is complete.</p>
          )}
        </div>
      </div>
    </div>
  );
}