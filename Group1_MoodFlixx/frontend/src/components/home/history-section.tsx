"use client";

import React, { useEffect, useState } from "react";
import { getHistory } from "@/lib/actions";
import Image from "next/image";
import type { MovieType } from "@/lib/movies";

const MovieCard = ({ movie }: { movie: MovieType }) => {
  return (
    <div className="relative z-0 aspect-video w-full min-w-[400px] rounded-lg border border-zinc-100/10">
      <Image
        src={`https://image.tmdb.org/t/p/w1920/${movie.poster_path}`}
        width={1920}
        height={1080}
        alt={movie.title}
        className="h-full w-full rounded-lg object-cover opacity-30"
      />
      <div className="absolute bottom-0 left-0 z-10 flex h-full w-full items-end justify-between rounded-lg bg-gradient-to-t from-zinc-900/90 p-5">
        <div className="text-lg font-semibold">{movie.title}</div>
        <div className="font-satoshi text-sm font-semibold text-zinc-100/70">
          {movie.vote_average.toFixed(1)}
        </div>
      </div>
    </div>
  );
};

const HistorySection = () => {
  const [movies, setMovies] = useState<MovieType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const func = async () => {
      const res = await getHistory();
      console.log(res);

      if (!res) {
        setLoading(false);
        return;
      }

      setMovies(res);
    };

    void func();
  }, []);

  useEffect(() => {
    console.log(movies);
  }, [movies]);

  return (
    <div className="relative z-0 flex w-full flex-row items-stretch gap-5 pb-24 pl-24">
      <div className="flex w-[300px] shrink-0 flex-col gap-2.5">
        <div className="font-satoshi text-2xl font-semibold">Watch again</div>
        <div className="font-hk text-base text-zinc-100/70">
          Continue where you left off
        </div>
      </div>
      <div className="relative z-0 flex h-full w-full flex-row items-center justify-start gap-5 overflow-x-scroll py-5">
        {movies.map((movie, i) => (
          <MovieCard movie={movie} key={i} />
        ))}
      </div>
      <div className="pointer-events-none absolute top-0 left-0 z-10 h-full w-full bg-gradient-to-r from-zinc-950/0 via-zinc-950/0 to-zinc-950/50"></div>
    </div>
  );
};

export default HistorySection;
