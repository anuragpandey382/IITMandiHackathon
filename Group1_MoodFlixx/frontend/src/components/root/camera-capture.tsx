"use client";

import { useEffect, useRef, useState } from "react";

export default function CameraCapture() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [photoURL, setPhotoURL] = useState<string | null>(null);

  // Start the camera
  useEffect(() => {
    const startCamera = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    };

    void startCamera();
  }, []);

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    if (context) {
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataURL = canvas.toDataURL("image/png");
      setPhotoURL(dataURL);
    }
  };

  return (
    <div className="space-y-4 p-4 text-center">
      <video
        ref={videoRef}
        autoPlay
        className="w-[400px] max-w-full rounded-lg"
      />
      <canvas ref={canvasRef} className="hidden" />

      <div>
        <button
          onClick={capturePhoto}
          className="rounded bg-blue-600 px-4 py-2 text-white"
        >
          Take Photo
        </button>
      </div>

      {photoURL && (
        <div className="mt-4">
          <img
            src={photoURL}
            alt="Captured"
            className="rounded border shadow"
          />
          <a
            href={photoURL}
            download="photo.png"
            className="mt-2 block text-blue-500 underline"
          >
            Download Photo
          </a>
        </div>
      )}
    </div>
  );
}
