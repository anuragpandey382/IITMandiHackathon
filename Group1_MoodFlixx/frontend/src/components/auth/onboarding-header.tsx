import React from "react";
import Image from "next/image";
import ImgBig from "public/pic-big.jpg";

const OnboardingHeader = () => {
  return (
    <div className="relative z-0 flex h-[50vh] w-screen flex-col items-center justify-center p-12">
      <Image
        src={ImgBig}
        alt={"Sample Pic"}
        className="absolute top-0 left-0 -z-20 h-full w-full"
      />
      <div className="absolute top-0 left-0 -z-10 h-full w-full bg-gradient-to-b from-zinc-950/50 to-zinc-950"></div>
      <div className="font-satoshi text-7xl font-bold tracking-wider uppercase">
        onboarding
      </div>
      <div className="font-hk max-w-[700px] pt-2.5 text-center text-base font-normal text-zinc-100/70">
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus
        aspernatur at ducimus eveniet, minima modi.
      </div>
    </div>
  );
};

export default OnboardingHeader;
