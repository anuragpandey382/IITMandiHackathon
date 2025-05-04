"use client";

import React, { useState } from "react";
import { addAccount } from "@/lib/actions";
import OnboardingHeader from "@/components/auth/onboarding-header";
import { useRouter } from "next/navigation";
import ChooseMovies from "@/components/onboarding/choose-movies";
import type { MovieType } from "@/lib/movies";

const OnboardingPage = () => {
  const [loc, setLoc] = useState("");
  const [lang, setLang] = useState("");

  const [chosen, setChosen] = useState<MovieType[]>([]);

  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const history = chosen.map((movie) => ({ ...movie, rating: 5 }));
    void addAccount({ loc, lang, currHistory: history });
    router.push("/");
  };

  return (
    <div>
      <OnboardingHeader />
      <div className="flex w-full flex-col items-center justify-center gap-12 px-12 pb-24">
        <div className="font-hk max-w-[800px] text-center text-base font-medium text-zinc-100/70">
          Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ab alias
          asperiores dolorum ipsa maiores modi obcaecati quas temporibus
          veritatis. Amet aperiam ea et eveniet ex nihil nobis sed soluta vero!
        </div>
        <form
          className="grid w-full max-w-[1200px] grid-cols-2 gap-5"
          onSubmit={handleSubmit}
        >
          <div className="flex flex-col gap-1">
            <div className="font-hk text-lg font-semibold">
              Enter your location
            </div>
            <input
              type="text"
              id="location"
              name="location"
              className="font-hk rounded-md border border-zinc-100/10 bg-zinc-900 px-5 py-2.5 text-sm text-zinc-100 outline-none"
              placeholder="eg: India"
              value={loc}
              onChange={(e) => setLoc(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <div className="font-hk text-lg font-semibold">Enter language</div>
            <input
              type="text"
              id="language"
              name="language"
              className="font-hk rounded-md border border-zinc-100/10 bg-zinc-900 px-5 py-2.5 text-sm text-zinc-100 outline-none"
              placeholder="eg: Hindi, English, ..."
              value={lang}
              onChange={(e) => setLang(e.target.value)}
            />
          </div>
          <ChooseMovies chosen={chosen} setChosen={setChosen} />
          <div className="col-span-2 mt-5 flex justify-center">
            <input
              type="submit"
              className="cursor-pointer rounded-md bg-gradient-to-bl from-rose-700 to-sky-600 px-5 py-2.5 font-medium"
              value="Submit"
            />
          </div>
        </form>
      </div>
    </div>
  );
};

export default OnboardingPage;
