"use client";

import React from "react";
import { useAuth } from "@/context/auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import ImgBig from "../../../public/pic-big.jpg";

const AccountPage = () => {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    redirect("/");
    // TODO: Handle redirect to login page
  }

  const handleSignOut = async () => {
    try {
      await signOut();
      redirect("/");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  return (
    <main className="relative z-0 h-dvh w-full overflow-x-clip bg-zinc-950 px-5 pt-24 pb-12 sm:px-12 md:pt-36 lg:px-48">
      <Image
        src={ImgBig}
        alt={"Sample pic"}
        className="absolute top-0 left-0 -z-20 h-full w-full object-cover object-center"
      />
      <div className="absolute top-0 left-0 -z-10 h-full w-full bg-gradient-to-b from-zinc-950/50 to-zinc-950"></div>
      <div className="flex h-full w-full flex-col justify-between gap-5 overflow-clip md:flex-row">
        <div className="flex h-fit shrink-0 flex-col gap-5 p-12">
          <Image
            src={user.photoURL ?? ""}
            width={400}
            height={400}
            alt={"User photo"}
            className="h-24 w-24 rounded-full object-cover object-center"
          />
          <div className="font-hk text-4xl font-bold">
            Hello, {user.displayName?.split(" ")[0]}
          </div>
          <div
            onClick={handleSignOut}
            className="font-satoshi mt-5 w-fit cursor-pointer rounded-full bg-rose-900 px-8 py-2.5 text-base font-semibold tracking-wider uppercase"
          >
            sign out
          </div>
        </div>
        <div className="h-full w-full rounded-2xl border border-zinc-100/10 bg-zinc-950/10 px-12 py-12 backdrop-blur-2xl">
          hello settings section
        </div>
      </div>
    </main>
  );
};

export default AccountPage;
