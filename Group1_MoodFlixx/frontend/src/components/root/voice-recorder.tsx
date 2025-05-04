// components/VoiceRecorder.tsx
"use client";

import React, { type Dispatch, type SetStateAction, useRef } from "react";
import { Mic, MicOff } from "lucide-react";

interface Props {
  isRecording: boolean;
  setIsRecording: Dispatch<SetStateAction<boolean>>;
  setAudioURL: Dispatch<SetStateAction<string | null>>;
}

export default function VoiceRecorder({
  isRecording,
  setIsRecording,
  setAudioURL,
}: Props) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;

    audioChunks.current = [];

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.current.push(event.data);
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks.current, { type: "audio/webm" });
      const url = URL.createObjectURL(audioBlob);
      setAudioURL(url);
    };

    mediaRecorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  return (
    <div
      onClick={isRecording ? stopRecording : startRecording}
      className="h-full cursor-pointer rounded-xl bg-gradient-to-bl from-rose-700 to-sky-600 px-5 py-2.5 text-base font-semibold text-zinc-100 uppercase"
    >
      {isRecording ? <MicOff /> : <Mic />}
    </div>
  );
}
