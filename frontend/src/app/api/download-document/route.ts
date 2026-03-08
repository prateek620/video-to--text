import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const jobId = request.nextUrl.searchParams.get("job_id");
    const format = request.nextUrl.searchParams.get("format");

    if (!jobId || !format) {
      return NextResponse.json(
        { error: "job_id and format required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `http://localhost:8000/download-document?job_id=${jobId}&format=${format}`
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "Download failed" },
        { status: response.status }
      );
    }

    const buffer = await response.arrayBuffer();
    return new NextResponse(buffer, {
      headers: {
        "Content-Disposition": `attachment; filename="document.${format}"`,
        "Content-Type": "application/octet-stream",
      },
    });
  } catch (error) {
    console.error("Download error:", error);
    return NextResponse.json(
      { error: "Download failed" },
      { status: 500 }
    );
  }
}