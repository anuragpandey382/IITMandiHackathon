"use client"
import { useRouter, useSearchParams } from "next/navigation"
import ProcessVisualization from "@/components/process-visualization"

export default function ProcessingPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const fileName = searchParams.get("fileName") || "document.pdf"

  const handleProcessComplete = () => {
    router.push(`/results?fileName=${encodeURIComponent(fileName)}`)
  }

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <header className="border-b bg-white sticky top-0 z-50 shadow-sm">
        <div className="container flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-sm">TbEx</span>
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6]">
              TableEx Document Processor
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">
              Processing: <span className="font-medium text-[#1E3A8A]">{fileName}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <ProcessVisualization fileName={fileName} onProcessComplete={handleProcessComplete} />
      </main>

      <footer className="border-t bg-white">
        <div className=" px-4 py-6 md:px-6 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} TableEx Document Processor. All rights reserved.
          </p>
          <div className="flex items-center gap-4 mt-4 sm:mt-0">
            <p className="text-xs text-gray-400">Processing may take a few moments depending on document complexity</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
