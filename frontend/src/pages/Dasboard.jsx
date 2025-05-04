import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Appbar } from "../components/Appbar";
import { motion } from "framer-motion";

export const Dashboard = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [detectionLoading, setDetectionLoading] = useState(false); 
  const [errorMessage, setErrorMessage] = useState("");
  const [detectedLanguage, setDetectedLanguage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [result, setResult] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const detectionIntervalRef = useRef(null);
  const token = localStorage.getItem("token");
  const isLoggedIn = !!token;
  const [audioUrl, setAudioUrl] = useState(null); 
  const [audioDuration, setAudioDuration] = useState(0);

  // Define backend URLs (adjust if needed)
const BACKEND_UPLOAD_URL = "http://localhost:8787/upload-audio-frontend";
const BACKEND_GET_LANGUAGE_URL = "http://localhost:8787/get-detected-language"
  useEffect(() => {
    const scanData = sessionStorage.getItem("scanData");
    if (scanData) {
      try {
        const parsed = JSON.parse(scanData);
        setDetectedLanguage(parsed.language || "Language not found");
        setConfidence(parsed.confidence || 0);
      } catch {
        setDetectedLanguage("Language not found");
      }
    }
  }, [loading]);

  useEffect(() => {
    if (isRecording) {
      setRecordingTime(0);
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);
    } else {
      clearInterval(timerIntervalRef.current);
      clearInterval(detectionIntervalRef.current);
    }
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (detectionIntervalRef.current) clearInterval(detectionIntervalRef.current);
    };
  }, [isRecording]);

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
    exit: { opacity: 0, y: -20, transition: { duration: 0.3 } },
  };

  const fadeInVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.5 } },
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      if (e.dataTransfer.files[0].type !== "audio/mpeg") {
        setErrorMessage("Only MP3 files are supported.");
        return;
      }
      setFile(e.dataTransfer.files[0]);
      setErrorMessage("");
    }
  };

  const fetchDetectedLanguage = async () => {
    try {
      const res = await fetch("http://localhost:8787/get-detected-language");
      const data = await res.json();
      if (data.success) {
        setDetectedLanguage(data.language);
        setConfidence(data.confidence || 0);
        sessionStorage.setItem("scanData", JSON.stringify(data));
      }
    } catch (err) {
      console.error("Error fetching language", err);
    }
  };

  const handleFileChange = async (e) => {
    const selected = e.target.files[0];
    if (selected && selected.type !== "audio/mpeg") {
      setErrorMessage("Only MP3 files are supported.");
      return;
    }

    setFile(selected);
    setErrorMessage("");
    setLoading(true);

    const formData = new FormData();
    formData.append("file", selected);

    try {
      const response = await fetch("http://localhost:8787/upload-audio-frontend", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.language) {
        setDetectedLanguage(data.language);
      }
      if (data.confidence !== undefined) {
        setConfidence(data.confidence);
      }
      sessionStorage.setItem("scanData", JSON.stringify(data));
    } catch (error) {
      console.error("Upload error:", error);
      setErrorMessage("Failed to upload audio. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  

  const sendAudioChunkForDetection = async (blob) => {
    const formData = new FormData();
    formData.append("file", blob, "chunk.webm");

    try {
      const response = await fetch("http://localhost:8787/upload-audio-frontend", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.language) {
          setDetectedLanguage(data.language);
        }
        if (data.confidence !== undefined) {
          setConfidence(data.confidence);
        }
        sessionStorage.setItem("scanData", JSON.stringify(data));
      }
    } catch (error) {
      console.error("Chunk upload error:", error);
    }
  };

  const startRecording = async () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
      setAudioDuration(0);
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
        if (mediaRecorder.state === "recording") {
          const audioBlob = new Blob([e.data], { type: 'audio/webm' });
          sendAudioChunkForDetection(audioBlob);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const recordedFile = new File([audioBlob], "recorded.webm", { type: 'audio/webm' });
        setFile(recordedFile);
        
        // Create URL for audio playback
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        
        // Set audio duration to the recording time
        setAudioDuration(recordingTime);
      };

      mediaRecorder.start();

      detectionIntervalRef.current = setInterval(() => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.requestData();
        }
      }, 5000);

      setIsRecording(true);
    } catch (error) {
      setErrorMessage("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    setIsRecording(false);
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" exit="exit" className="bg-lightBg dark:bg-darkBg min-h-screen flex flex-col">
      <Appbar />
      <motion.div variants={fadeInVariants} initial="hidden" animate="visible" className="flex flex-col items-center justify-center flex-grow text-center px-6">
        <motion.h1 className="text-5xl md:text-3xl font-extrabold text-lightText dark:text-darkText cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => navigate("/")}>
          Voice of the Nation
        </motion.h1>
        <motion.p className="mt-4 max-w-2xl text-xl md:text-lg text-gray-700 dark:text-gray-300" initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.3, duration: 0.5 } }}>
          A system that identifies Indian languages from speech, enabling fast and accurate language recognition for voice-driven applications.
        </motion.p>

        {errorMessage && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 w-full max-w-lg bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg dark:bg-red-900 dark:text-red-200 dark:border-red-800">
            <div className="flex items-start">
              <svg className="w-5 h-5 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path>
              </svg>
              <p>{errorMessage}</p>
            </div>
          </motion.div>
        )}

        <motion.div className="mt-6 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-8" initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.5, duration: 0.5 } }}>
          <div className={`flex flex-col items-center p-6 border-2 border-dashed rounded-lg ${dragActive ? "border-blue-600" : errorMessage ? "border-red-400 dark:border-red-800" : "border-gray-400 dark:border-gray-600"}`} onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}>
            <p className="text-gray-600 dark:text-gray-300 mb-4">{file ? `Selected File: ${file.name}` : "Drag & drop your MP3 file here or click to upload"}</p>
            <input type="file" accept="audio/mp3" className="hidden" id="fileInput" onChange={handleFileChange} />
            <label htmlFor="fileInput" className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Choose an MP3 File</label>

            <div className="mt-4 flex flex-col items-center">
              <button onClick={isRecording ? stopRecording : startRecording} className={`${isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'} text-white px-4 py-2 rounded-lg flex items-center`}>
                {isRecording ? <><span className="mr-2">⬤</span> Stop Recording</> : "Record Audio"}
              </button>
              {isRecording && (
                <div className="mt-2 text-red-600 dark:text-red-400 font-medium flex items-center">
                  <span className="animate-pulse mr-2">⬤</span> Recording: {formatTime(recordingTime)}
                </div>
              )}
            </div>
            {/* Audio Player - shows only when audio is available */}
{audioUrl && (
  <div className="mt-4 w-full flex flex-col items-center">
    <audio 
      src={audioUrl} 
      controls 
      className="w-full max-w-md mt-2" 
    />

  </div>
)}
          </div>
            

           <div className="flex flex-col items-center justify-center p-6 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 shadow-md">
            <motion.button onClick={fetchDetectedLanguage} whileTap={{ scale: 0.95 }} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Detected Language:
            </motion.button>
            <p className="text-lg text-gray-700 dark:text-gray-300 mt-4">
              {loading ? "Analyzing..." : detectedLanguage || ""}
            </p>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
};
