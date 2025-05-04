"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import VoiceRecorder from "@/components/root/voice-recorder";
import { useRecommendations } from "@/context/recommendations";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";

const SearchWidget = () => {
  const [toggle, setToggle] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [value, setValue] = useState("");

  const router = useRouter();

  const { recommendations, setRecommendations } = useRecommendations();

  const [loading, setLoading] = useState(false);

  const initiateAudio = async () => {
    setLoading(true);
    const formData = new FormData();
    if (audioURL) {
      const blob = await fetch(audioURL).then((r) => r.blob());
      const file = new File([blob], "recording.webm", { type: "audio/webm" });

      formData.append("file", file);
    }

    const res = await fetch("http://localhost:8000/api/chatbot", {
      method: "POST",
      body: formData,
    });

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const data = await res.json();

    console.log("Upload success:", data.results);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    setRecommendations(data.results);
    setLoading(false);
    setToggle(false);
    router.push("/recommendations");
  };

  const initiateText = async () => {
    setLoading(true);
    const formData = new FormData();
    formData.append("text", value);

    const res = await fetch("http://localhost:8000/api/chatbot", {
      method: "POST",
      body: formData,
    });

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const data = await res.json();

    console.log("Upload success:", data.results);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    setRecommendations(data.results);
    setLoading(false);
    setToggle(false);
    router.push("/recommendations");
  };

  return (
    <div className="font-satoshi hidden h-full w-full flex-col items-start justify-between overflow-x-clip rounded-2xl border border-zinc-100/[0.2] bg-zinc-900/[0.3] text-zinc-100/90 backdrop-blur-2xl md:flex">
      <motion.div className="flex w-full items-start justify-between gap-12 overflow-x-clip font-medium">
        <input
          type="text"
          className="hidden h-min w-full px-5 py-2.5 outline-none md:block"
          placeholder={"What's on your mind?"}
          onFocus={() => setToggle(true)}
          onChange={(e) => setValue(e.target.value)}
          value={value}
        ></input>
        <VoiceRecorder
          isRecording={isRecording}
          setIsRecording={setIsRecording}
          setAudioURL={setAudioURL}
        />
      </motion.div>
      <motion.div
        className="relative z-0 w-full overflow-x-clip overflow-y-scroll"
        initial={{ height: 0 }}
        animate={{ height: toggle ? "50vh" : 0 }}
      >
        <div className="font-hk mt-2.5 space-y-2.5 px-5 text-sm font-medium text-zinc-100">
          <div
            className="cursor-pointer rounded-lg bg-zinc-900/20 px-5 py-2.5 text-zinc-100"
            onClick={() =>
              setValue(
                "I am feeling very happy, and I am in the mood for some jam-packed action movies",
              )
            }
          >
            &quot;I am feeling very happy, and I am in the mood for some
            jam-packed action movies&quot;
          </div>
          <div
            className="cursor-pointer rounded-lg bg-zinc-900/20 px-5 py-2.5 text-zinc-100"
            onClick={() =>
              setValue("Show me some Amitabh Bachchan action movies")
            }
          >
            &quot;Show me some Amitabh Bachchan action movies&quot;
          </div>
        </div>
        <div className="mt-5 flex items-center gap-2.5 px-5">
          {audioURL && (
            <div
              onClick={initiateAudio}
              className="h-full cursor-pointer rounded-lg bg-gradient-to-bl from-rose-700 to-sky-600 px-5 py-2.5 text-sm font-semibold text-zinc-100 uppercase"
            >
              Send Audio
            </div>
          )}
          {value && (
            <div
              onClick={initiateText}
              className="h-full cursor-pointer rounded-lg bg-gradient-to-bl from-rose-700 to-sky-600 px-5 py-2.5 text-sm font-semibold text-zinc-100 uppercase"
            >
              Send Text
            </div>
          )}
          {loading && (
            <div className="text-sm font-medium uppercase">loading...</div>
          )}
          <div
            onClick={() => setToggle(false)}
            className="absolute right-5 bottom-5 w-fit cursor-pointer rounded-md"
          >
            <X />
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SearchWidget;
