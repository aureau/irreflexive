const API_BASE_URL = process.env.IRREFLEXIVE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/articles/latest`, {
      cache: "no-store",
    });

    const payload = await response.json();
    return Response.json(payload, { status: response.status });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown API error";
    return Response.json(
      {
        articles: [],
        errors: [{ outlet: "Frontend proxy", message }],
        fetched_at: new Date().toISOString(),
      },
      { status: 502 }
    );
  }
}
