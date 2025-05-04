"use client";

import React, {
  createContext,
  type ReactNode,
  useContext,
  useState,
} from "react";
import type { MovieData } from "@/app/recommendations/page";

type RecommendationsContextType = {
  recommendations: string[];
  setRecommendations: (movies: string[]) => void;
  movies: MovieData[];
  setMovies: (movies: MovieData[]) => void;
};

const RecommendationsContext = createContext<
  RecommendationsContextType | undefined
>(undefined);

export const RecommendationsProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [recommendations, setRecommendations] = useState<string[]>([]); // Initialize as empty or with default 10
  const [movies, setMovies] = useState<MovieData[]>([]);

  return (
    <RecommendationsContext.Provider
      value={{ recommendations, setRecommendations, movies, setMovies }}
    >
      {children}
    </RecommendationsContext.Provider>
  );
};

export const useRecommendations = () => {
  const context = useContext(RecommendationsContext);
  if (!context) {
    throw new Error(
      "useRecommendations must be used within a RecommendationsProvider",
    );
  }
  return context;
};
