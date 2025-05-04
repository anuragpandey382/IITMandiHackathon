import React from "react";
import Link from "next/link";

const WatchNow = ({ id }: { id: string }) => {
  return (
    <Link
      className={`font-satoshi mb-12 w-fit cursor-pointer rounded-md border border-zinc-100/[0.1] bg-blue-950 px-5 py-2 text-lg font-semibold`}
      href={"/"}
      target="_blank"
    >
      Watch now
    </Link>
  );
};

export default WatchNow;
