"use client";

import React from "react";
import { useRecommendations } from "@/context/recommendations";
import ImgBig from "public/pic-big.jpg";
import Image from "next/image";
import { getMovieByImdbId, type MovieType } from "@/lib/movies";
import SmallCard from "@/components/recommendations/small-card";

export interface MovieData extends MovieType {
  imdb_id: string;
}

const Page = () => {
  const { recommendations, movies, setMovies } = useRecommendations();

  React.useEffect(() => {
    const fetchMovies = async () => {
      const movieData = await Promise.all(
        recommendations.map((id) => getMovieByImdbId(id)),
      );

      const filteredMovieData: MovieData[] = movieData
        .map((el, i) => {
          if (!el.movie_results?.[0]) return undefined;
          return {
            ...el.movie_results[0],
            imdb_id: recommendations[i],
          };
        })
        .filter((item): item is MovieData => item !== undefined);

      const MorefilteredMovieData = filteredMovieData.filter(
        (el) => el !== undefined,
      );
      setMovies(MorefilteredMovieData);
    };
    void fetchMovies();
  }, [recommendations, setMovies]);

  if (!movies.length)
    return (
      <div className="flex h-dvh w-screen items-center justify-center bg-zinc-950">
        loading
      </div>
    );

  return (
    <div className="flex h-full w-full flex-col gap-12 p-12">
      <div className="relative z-0 flex w-full gap-5 overflow-clip rounded-2xl border border-zinc-100/10 px-12 py-48 text-zinc-100">
        <Image
          src={
            movies?.[0]
              ? `https://image.tmdb.org/t/p/w1920/${movies[0].backdrop_path}`
              : ImgBig
          }
          width={1920}
          height={1080}
          alt={movies?.[0] ? movies[0].title : "Loading Movie"}
          className="absolute top-0 left-0 -z-10 h-full w-full object-cover opacity-50"
        />
        <div className="flex flex-col">
          <div className="font-hk w-fit rounded-full bg-amber-500/70 px-2 py-1 text-xs font-semibold">
            Top recommendation
          </div>
          <div className="font-satoshi text-6xl font-bold">
            {movies?.[0] ? movies[0].title : "Loading Movie"}
          </div>
          <div className="mt-5 max-w-[700px] text-base font-medium text-zinc-100/70">
            {movies?.[0]
              ? movies[0].overview
              : "Sit tight, we're working on your recommendations."}
          </div>
          <div className="mt-12 w-fit rounded-md border border-zinc-100/10 bg-blue-900 px-5 py-2.5 text-lg font-medium">
            Watch now
          </div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-5 pt-12">
        {movies.map((movie) => (
          <SmallCard movie={movie} key={movie.id} />
        ))}
      </div>
    </div>
  );
};

export default Page;
