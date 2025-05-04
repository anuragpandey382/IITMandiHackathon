"use client";

import React from "react";
import { getPlaylistRecommendations } from "@/lib/actions";

const TestPage = () => {
  const getMyPlaylist = async () => {
    const response = await getPlaylistRecommendations();

    console.log(response.results);
  };

  return (
    <div className="pt-40">
      <div className="bg-red-300 p-5" onClick={getMyPlaylist}>
        playlist
      </div>
    </div>
  );
};

export default TestPage;
