"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { FileUp, UploadIcon, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState, useCallback } from "react"

export function Upload() {
  const router = useRouter()
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [showProgress, setShowProgress] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0]
      handleFile(droppedFile)
    }
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0]
      handleFile(selectedFile)
    }
  }, [])

  const handleFile = useCallback((selectedFile: File) => {
    const fileType = selectedFile.type;
  
    if (
      fileType === "application/pdf" ||
      fileType === "image/png" ||
      fileType === "image/jpeg"
    ) {
      setFile(selectedFile); // Assume setFile is in scope
    } else {
      alert("Please upload a PDF, PNG, or JPG file.");
    }
  }, []);
  

  const handleUpload = useCallback(async () => {
    if (!file) return;

    const fileType = file.type;
    let endpoint = '';
    let formKey = '';

    if (fileType === 'application/pdf') {
      endpoint = 'http://localhost:5000/processPdf';
      formKey = 'pdf';
    } else if (fileType === 'image/png' || fileType === 'image/jpeg') {
      endpoint = 'http://localhost:5000/processImage';
      formKey = 'image';
    } else {
      alert('Unsupported file type');
      return;
    }

    const formData = new FormData();
    
    formData.append(formKey, file);
    console.log('Form data:', formData.get(formKey))
    
    try {
      setIsUploading(true);
      setShowProgress(true);
      
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 10;
        console.log('Progress:', progress);
        if (progress >= 90) { 
          clearInterval(interval);
        }
        setUploadProgress(progress);
        
        // if (progress >= 100) {
        //   progress = 100;
        //   setTimeout(() => {
        //     router.push(`/processing?fileName=${encodeURIComponent(file.name)}`);
        //   }, 500);
        // }
      }, 200);
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('Server response:', data);
      await localStorage.setItem("processingResponse", JSON.stringify(data));
      progress=100;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setTimeout(() => {
          router.push(`/processing?fileName=${encodeURIComponent(file.name)}`);
        }, 500);
      }
      setUploadProgress(progress);
      // Simulate upload progress

    } catch (err) {
      console.error('Upload error:', err);
      alert('Failed to upload.');
      setShowProgress(false);
      setIsUploading(false);
      window.location.reload();
    } finally {
      setIsUploading(false);
    }
  }, [file, router]);
  

  const clearFile = useCallback(() => {
    setFile(null)
    setUploadProgress(0)
    setShowProgress(false)
  }, [])

  return (
    <Card
      className={`border-2 ${
        isDragging ? "border-[#1E3A8A] border-dashed bg-[#1E3A8A]/5" : "border-gray-200"
      } shadow-lg transition-all duration-200`}
    >
      <CardContent className="p-6">
        <div
          className="flex flex-col items-center justify-center gap-4 py-8"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {!file ? (
            <>
              <div className="rounded-full bg-[#1E3A8A]/10 p-4 animate-pulse">
                <FileUp className="h-8 w-8 text-[#1E3A8A]" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-[#1E3A8A]">Drag & Drop your file here</h3>
                <p className="text-sm text-gray-500 mt-1">Supports PDF, PNG, and JPG files up to 10MB</p>
              </div>
              <div className="flex flex-col items-center gap-2 sm:flex-row">
                <label htmlFor="file-upload">
                  <Button
                    variant="outline"
                    className="cursor-pointer border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10"
                    size="lg"
                    asChild
                  >
                    <span>Browse Files</span>
                  </Button>
                  <input
                    id="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileChange}
                  />
                </label>
                <span className="text-sm text-gray-500">or</span>
                <Button
                  className="bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity cursor-pointer"
                  size="lg"
                  onClick={() => document.getElementById("file-upload")?.click()}
                >
                  Upload Document
                </Button>
              </div>
            </>
          ) : (
            <div className="w-full space-y-4">
              <div className="flex items-center justify-between p-4 bg-[#1E3A8A]/5 rounded-lg border border-[#1E3A8A]/20">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-[#1E3A8A]/10 rounded-md">
                    <FileUp className="h-5 w-5 text-[#1E3A8A]" />
                  </div>
                  <div>
                    <p className="font-medium text-[#1E3A8A] truncate max-w-[200px]">{file.name}</p>
                    <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 text-gray-500 hover:text-red-500"
                  onClick={clearFile}
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Remove file</span>
                </Button>
              </div>

              {showProgress && (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#1E3A8A] font-medium">Uploading...</span>
                    <span className="text-gray-500">{Math.round(uploadProgress)}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}

              <div className="flex justify-center">
                <Button
                  className="w-full gap-2 bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity"
                  size="lg"
                  onClick={handleUpload}
                  disabled={isUploading}
                >
                  {isUploading ? (
                    <>Uploading Document...</>
                  ) : (
                    <>
                      <UploadIcon className="h-4 w-4" />
                      Process Document
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
