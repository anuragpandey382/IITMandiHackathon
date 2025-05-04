"use client";

import React, {
  type Dispatch,
  type SetStateAction,
  useEffect,
  useState,
} from "react";
import { chunkArray, getPopularMovies, type MovieType } from "@/lib/movies";
import Image from "next/image";
import toast from "react-hot-toast";

const MovieCard = ({
  movie,
  i,
  setIndex,
  setChosen,
  disabled,
}: {
  movie: MovieType;
  i: number;
  setIndex: Dispatch<SetStateAction<number>>;
  setChosen: Dispatch<SetStateAction<MovieType[]>>;
  disabled: boolean;
}) => {
  const likeMovie = () => {
    setChosen((prev) => [...prev, movie]);
    setIndex(i + 1);
  };

  return (
    <div
      className={`relative z-0 flex cursor-pointer flex-col items-center justify-center ${disabled && "pointer-events-none"}`}
      onClick={likeMovie}
    >
      <Image
        src={`https://image.tmdb.org/t/p/w500/${movie.poster_path}`}
        width={400}
        height={600}
        alt={movie.title}
        className="w-full rounded-lg border border-zinc-100/10 bg-zinc-900 object-cover"
      />
    </div>
  );
};

const MovieRow = ({
  row,
  i,
  setIndex,
  setChosen,
}: {
  row: MovieType[];
  i: number;
  setIndex: Dispatch<SetStateAction<number>>;
  setChosen: Dispatch<SetStateAction<MovieType[]>>;
}) => {
  return (
    <div
      key={i}
      className="grid w-full grid-cols-1 gap-5 sm:grid-cols-2 md:grid-cols-4"
    >
      {row.map((movie) => (
        <MovieCard
          i={i}
          setIndex={setIndex}
          movie={movie}
          key={movie.id}
          disabled={false}
          setChosen={setChosen}
        />
      ))}
    </div>
  );
};

const ChooseMovies = ({
  chosen,
  setChosen,
}: {
  chosen: MovieType[];
  setChosen: Dispatch<SetStateAction<MovieType[]>>;
}) => {
  const [movies, setMovies] = useState<MovieType[][]>();
  const [loading, setLoading] = useState(true);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const fetchMovies = async () => {
      setLoading(true);
      try {
        const data = await getPopularMovies();
        const rows = chunkArray(data, 4);
        setMovies(rows);
      } catch (error) {
        toast.error("Error fetching movies. Check console");
        console.log(error);
      }
      setLoading(false);
    };

    void fetchMovies();
  }, []);

  useEffect(() => {
    if (index >= 4) {
      const chosenMovies = movies?.flatMap((row) => row).slice(0, 4);
      console.log("hidden", chosenMovies);
    }
  }, [index, movies]);

  if (loading) return <div>Loading...</div>;
  if (!movies) return <div>No movies found</div>;

  if (index < 4)
    return (
      <div className="col-span-2 w-full p-12 px-5 sm:px-12">
        {movies[index] && (
          <MovieRow
            setIndex={setIndex}
            setChosen={setChosen}
            row={movies[index]}
            i={index}
            key={index}
          />
        )}
      </div>
    );

  return (
    <div className="col-span-2 grid w-full grid-cols-4 gap-5 p-12 px-5 sm:px-12">
      {chosen.map((el, i) => (
        <MovieCard
          movie={el}
          i={i}
          setIndex={setIndex}
          setChosen={setChosen}
          disabled={true}
          key={i}
        />
      ))}
    </div>
  );
};

export default ChooseMovies;
