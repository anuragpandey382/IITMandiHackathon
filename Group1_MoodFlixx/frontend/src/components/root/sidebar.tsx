"use client";

import React, {
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useState,
} from "react";
import { motion } from "motion/react";
import {
  History,
  HomeIcon,
  MoreVertical,
  TelescopeIcon,
  User,
  X,
} from "lucide-react";
import SignInButton from "@/components/auth/signin-button";
import SearchWidget from "@/components/root/search-widget";
import Link from "next/link";

const SidebarLink = ({
  icon,
  href,
  title,
  setToggle,
}: {
  icon: ReactNode;
  href: string;
  title: string;
  setToggle: Dispatch<SetStateAction<boolean>>;
}) => {
  return (
    <Link
      href={href}
      onClick={() => setToggle(false)}
      className="font-satoshi flex items-center gap-5 text-lg font-medium tracking-wider uppercase"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-100/[0.2] bg-zinc-950/[0.2] text-zinc-100">
        {icon}
      </div>
      {title}
    </Link>
  );
};

const SidebarMenu = ({
  toggle,
  setToggle,
}: {
  toggle: boolean;
  setToggle: Dispatch<SetStateAction<boolean>>;
}) => {
  return (
    <div className="fixed top-0 left-0 z-50 h-5 w-screen px-5 py-5 sm:px-24 lg:px-48">
      <div className="flex w-full items-start justify-start gap-5 sm:gap-12 md:justify-center">
        <div
          className="font-satoshi flex shrink-0 cursor-pointer items-center justify-between gap-2.5 text-sm font-semibold uppercase"
          onClick={() => setToggle(!toggle)}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-100/[0.2] bg-zinc-950/[0.2] text-zinc-100">
            {toggle ? <X /> : <MoreVertical />}
          </div>
          {toggle ? "close" : "menu"}
        </div>
        <SearchWidget />
      </div>
    </div>
  );
};

const Sidebar = () => {
  const [toggle, setToggle] = useState(false);

  return (
    <>
      <SidebarMenu toggle={toggle} setToggle={setToggle} />
      <motion.div
        initial={{
          x: "-100%",
        }}
        animate={{
          x: toggle ? 0 : "-100%",
        }}
        transition={{
          duration: 0.5,
          ease: [0.25, 1, 0.5, 1],
        }}
        className="fixed z-40 flex h-dvh bg-zinc-950/[0.5] pr-48 backdrop-blur-lg"
      >
        <div className="flex h-full flex-col justify-between px-12 py-24">
          <div className="flex flex-col items-start gap-12">
            <div className="mt-2.5 space-y-2.5">
              <SignInButton />
              <div className="font-satoshi max-w-[500px] text-sm leading-normal font-medium text-zinc-100/70">
                Create an account to save your preferences.
              </div>
            </div>
            <div className="flex flex-col gap-5">
              <SidebarLink
                setToggle={setToggle}
                icon={<HomeIcon />}
                title={"Home"}
                href={"/"}
              />
              <SidebarLink
                setToggle={setToggle}
                icon={<TelescopeIcon />}
                title={"explore"}
                href={"/movies"}
              />
              <SidebarLink
                setToggle={setToggle}
                icon={<User />}
                title={"account"}
                href={"/account"}
              />
              <SidebarLink
                setToggle={setToggle}
                icon={<History />}
                title={"history"}
                href={"/"}
              />
            </div>
          </div>
          <div className="font-satoshi max-w-[400px] text-sm leading-normal font-medium text-zinc-100/50">
            MoodFlixx is a smart movie recommendation engine that requires
            minimal input from the user&apos;s side, using a combination of user
            ratings and a single text prompt to generate the perfect movie night
            for you.
          </div>
        </div>
      </motion.div>
    </>
  );
};

export default Sidebar;
