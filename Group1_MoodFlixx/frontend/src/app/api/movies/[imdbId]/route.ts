// app/api/movies/[imdbId]/route.ts
import { NextResponse } from "next/server";

export async function GET(
  _req: Request,
  { params }: { params: { imdbId: string } },
) {
  const apiKey = process.env.TMDB_API_KEY;
  const { imdbId } = params;

  console.log("hello");

  try {
    const res = await fetch(
      `https://api.themoviedb.org/3/find/${imdbId}?external_source=imdb_id&api_key=b63578506001c86a3ab23ee40393e164`,
    );

    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to fetch from TMDB" },
        { status: 500 },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("TMDB fetch error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
