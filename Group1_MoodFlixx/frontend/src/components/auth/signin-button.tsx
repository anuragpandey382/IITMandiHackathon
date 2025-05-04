"use client";

import { signInWithGoogle } from "@/lib/auth";
import { useRouter } from "next/navigation";
import React from "react";
import { Lock } from "lucide-react";
import { useAuth } from "@/context/auth";

export default function SignInButton() {
  const router = useRouter();
  const { user, signOut, loading } = useAuth();

  const handleSignIn = async () => {
    try {
      const user = await signInWithGoogle();
      console.log("Signed in user:", user);
      if (user) router.push("/onboarding");
    } catch (err) {
      alert("Failed to sign in. Check console for details.");
      console.error(err);
    }
  };

  return (
    <div
      className="font-satoshi flex w-fit cursor-pointer items-center justify-center gap-5 rounded-full bg-gradient-to-bl from-rose-700 to-sky-600 px-8 py-2.5 text-base font-bold tracking-wider text-zinc-100 uppercase"
      onClick={user ? signOut : handleSignIn}
    >
      {!user && <Lock />}
      {user ? "sign out" : "sign in with google"}
    </div>
  );
}
