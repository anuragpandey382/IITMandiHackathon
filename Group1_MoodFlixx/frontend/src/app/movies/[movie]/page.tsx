"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getMovieByImdbId, type MovieType } from "@/lib/movies";
import Image from "next/image";
import ReviewWidget from "@/components/movies/review-widget";
import WatchNow from "@/components/movies/watch-now";
import toast from "react-hot-toast";

const MoviePage = () => {
  const movieId = useParams().movie;
  const [movie, setMovie] = useState<MovieType>();

  useEffect(() => {
    const fetchMovie = async () => {
      try {
        const data = await getMovieByImdbId(movieId as string);
        const movieData = data.movie_results[0];

        if (!movieData) {
          throw new Error("Movie not found");
        }

        setMovie(movieData);
      } catch (error) {
        toast.error("Error fetching movie. Check console");
        console.log(error);
      }
    };

    void fetchMovie();
  }, [movieId]);

  if (!movie) return <div>Loading...</div>;

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-5">
      <div className="relative -z-10 flex h-[90vh] w-full flex-row items-start justify-between gap-5 px-48 pt-48 pb-12">
        <Image
          src={`https://image.tmdb.org/t/p/w1920/${movie.backdrop_path}`}
          width={1920}
          height={1080}
          alt={movie.title}
          className="absolute top-0 left-0 -z-20 h-dvh w-full object-cover object-center"
        />
        <div className="absolute top-0 left-0 -z-10 h-dvh w-full bg-gradient-to-b from-zinc-950/20 to-zinc-950"></div>
        <div className="flex flex-col justify-center">
          <div className="w-fit rounded-md bg-amber-800 px-2.5 py-1 text-base font-semibold uppercase">
            {movie.vote_average.toFixed(1)}
          </div>
          <div className="font-satoshi max-w-[800px] text-6xl leading-normal font-bold tracking-[-1px]">
            {movie.title}
          </div>
          <div className="font-hk mb-12 max-w-[700px] text-base font-medium text-zinc-100/70">
            {movie.overview}
          </div>
          <WatchNow id={movieId as string} />
        </div>
      </div>
      <div className="flex w-full flex-col items-center justify-center gap-2.5 pb-24">
        <div className="font-satoshi text-4xl font-bold text-zinc-100">
          Rate this movie
        </div>
        <ReviewWidget movie={movie} />
      </div>
    </div>
  );
};

export default MoviePage;
