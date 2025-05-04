import React from "react";
import ImgBig from "public/pic-big.jpg";
import Image from "next/image";

const Page = () => {
  return (
    <main className="relative z-0 h-dvh w-full overflow-x-clip bg-zinc-950 px-5 pt-24 pb-12 sm:px-12 md:pt-36 lg:px-48">
      <Image
        src={ImgBig}
        alt={"Sample pic"}
        className="absolute top-0 left-0 -z-20 h-full w-full object-cover object-center"
      />
      <div className="absolute top-0 left-0 -z-10 h-full w-full bg-gradient-to-b from-zinc-950/50 via-zinc-950 to-zinc-950"></div>
      <div className="flex h-full w-full flex-col justify-between overflow-clip rounded-xl border border-zinc-100/10 backdrop-blur-2xl">
        hi
        <form className="flex w-full flex-row gap-5">
          <input
            type="text"
            className="w-full border-t border-t-zinc-100/10 px-5 py-2.5 outline-none"
            placeholder="Write your mind out"
          />
          <div className="shrink-0 bg-gradient-to-bl from-rose-700 to-sky-600 px-5 py-2.5 font-semibold uppercase">
            enter
          </div>
        </form>
      </div>
    </main>
  );
};

export default Page;
