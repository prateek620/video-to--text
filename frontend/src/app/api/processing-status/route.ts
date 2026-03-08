import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const jobId = request.nextUrl.searchParams.get("job_id");

    if (!jobId) {
      return NextResponse.json(
        { error: "job_id required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `http://localhost:8000/processing-status?job_id=${jobId}`
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "Status check failed" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Status check error:", error);
    return NextResponse.json(
      { error: "Status check failed" },
      { status: 500 }
    );
  }
}