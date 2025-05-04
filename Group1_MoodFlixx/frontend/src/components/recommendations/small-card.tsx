import React from "react";
import Image from "next/image";
import Link from "next/link";
import type { MovieData } from "@/app/recommendations/page";

const SmallCard = ({ movie }: { movie: MovieData }) => {
  return (
    <div className="relative z-0 aspect-video w-full rounded-lg border border-zinc-100/10">
      <Image
        src={`https://image.tmdb.org/t/p/w1920/${movie.poster_path}`}
        width={1920}
        height={1080}
        alt={movie.title}
        className="h-full w-full rounded-lg object-cover opacity-50"
      />
      <div className="absolute bottom-0 left-0 z-10 flex h-full w-full items-end justify-between rounded-lg bg-gradient-to-t from-zinc-900/90 p-5">
        <Link
          href={`/movies/${movie.imdb_id}`}
          className="font-satoshi text-xl font-bold text-zinc-100 hover:underline"
        >
          {movie.title}
        </Link>
        <div className="font-satoshi text-sm font-semibold text-zinc-100/70">
          {movie.vote_average.toFixed(1)}
        </div>
      </div>
    </div>
  );
};

export default SmallCard;
