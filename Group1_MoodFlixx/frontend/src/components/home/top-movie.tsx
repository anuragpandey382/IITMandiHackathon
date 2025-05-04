"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { getMovieByImdbId, type MovieType } from "@/lib/movies";
import ImgBig from "public/pic-big.jpg";
import toast from "react-hot-toast";

const TopMovie = () => {
  const [movie, setMovie] = useState<MovieType>();

  useEffect(() => {
    const fetchMovie = async () => {
      try {
        const data = await getMovieByImdbId("tt3566834");
        const movieData = data.movie_results[0];
        setMovie(movieData);
      } catch (error) {
        toast.error("Error fetching movie. Check console");
        console.log(error);
      }
    };

    void fetchMovie();
  }, []);

  useEffect(() => {
    if (movie) {
      console.log(movie);
    }
  }, [movie]);

  return (
    <div className="relative -z-10 h-[80vh] w-full">
      <Image
        src={
          movie
            ? `https://image.tmdb.org/t/p/w1920/${movie.backdrop_path}`
            : ImgBig
        }
        width={1920}
        height={1080}
        alt={movie?.title ?? "Loading Movies"}
        className="absolute top-0 left-0 -z-20 h-dvh w-full object-cover object-center"
      />
      <div className="absolute top-0 left-0 -z-10 h-dvh w-full bg-gradient-to-b from-zinc-950/30 via-zinc-950/70 to-zinc-950"></div>
      <div className="h-full w-full px-48 pt-24 pb-12">
        <div className="flex h-full w-full flex-col justify-center">
          <div className="w-fit rounded-md bg-amber-800 px-2.5 py-1 text-base font-semibold uppercase">
            {movie?.vote_average.toFixed(1) ?? 10.0}
          </div>
          <div className="font-satoshi max-w-[800px] text-6xl leading-normal font-bold tracking-[-1px]">
            {movie?.title ?? "Loading Movie"}
          </div>
          <div className="font-hk mb-12 max-w-[700px] text-base font-medium text-zinc-100/70">
            {movie?.overview ??
              "Hang tight while we fetch out latest recommendations for you."}
          </div>
          <div className="font-satoshi relative z-20 w-fit cursor-pointer rounded-md border border-zinc-100/[0.1] bg-blue-900 px-5 py-2 text-lg font-semibold">
            Start now
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopMovie;
