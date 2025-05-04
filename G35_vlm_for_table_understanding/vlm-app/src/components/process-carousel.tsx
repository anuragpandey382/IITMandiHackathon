"use client"

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useRouter } from "next/navigation"

// Process steps based on the flowchart
const processSteps = [
  {
    id: 1,
    image: "/placeholder.svg?height=200&width=200",
    caption: "PDF to Image",
    description: "Converting PDF documents into image format for processing",
    color: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  {
    id: 2,
    image: "/placeholder.svg?height=200&width=200",
    caption: "Table Detection",
    description: "Identifying and locating tables within the document",
    color: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  {
    id: 3,
    image: "/placeholder.svg?height=200&width=200",
    caption: "Structure Recognition",
    description: "Analyzing the document structure and layout",
    color: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  {
    id: 4,
    image: "/placeholder.svg?height=200&width=200",
    caption: "OCR",
    description: "Extracting text from images using Optical Character Recognition",
    color: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  {
    id: 5,
    image: "/placeholder.svg?height=200&width=200",
    caption: "Form Prompt",
    description: "Creating structured prompts based on document content",
    color: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  {
    id: 6,
    image: "/placeholder.svg?height=200&width=200",
    caption: "CSV Export",
    description: "Exporting structured data to CSV format",
    color: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  {
    id: 7,
    image: "/placeholder.svg?height=200&width=200",
    caption: "LLM Processing",
    description: "Using Large Language Models to interpret document content",
    color: "bg-green-50",
    borderColor: "border-green-200",
  },
]

interface ProcessCarouselProps {
  fileName: string
  onProcessComplete: () => void
}

export default function ProcessCarousel({ fileName, onProcessComplete }: ProcessCarouselProps) {
  const carouselRef = useRef<HTMLDivElement>(null)
  const [scrollPosition, setScrollPosition] = useState(0)
  const [activeStep, setActiveStep] = useState(0)
  const [isProcessing, setIsProcessing] = useState(true)
  const router = useRouter()

  const scrollAmount = 300 // Amount to scroll on each arrow click

  const scrollLeft = () => {
    if (carouselRef.current) {
      const newPosition = Math.max(0, scrollPosition - scrollAmount)
      carouselRef.current.scrollTo({
        left: newPosition,
        behavior: "smooth",
      })
      setScrollPosition(newPosition)
    }
  }

  const scrollRight = () => {
    if (carouselRef.current) {
      const maxScroll = carouselRef.current.scrollWidth - carouselRef.current.clientWidth
      const newPosition = Math.min(maxScroll, scrollPosition + scrollAmount)
      carouselRef.current.scrollTo({
        left: newPosition,
        behavior: "smooth",
      })
      setScrollPosition(newPosition)
    }
  }

  // Simulate processing through each step
  useEffect(() => {
    if (!isProcessing) return

    const interval = setInterval(() => {
      if (activeStep < processSteps.length) {
        setActiveStep((prev) => prev + 1)

        // Auto-scroll to keep active step visible
        if (carouselRef.current) {
          const stepWidth = 250 + 16 // card width + gap
          carouselRef.current.scrollTo({
            left: stepWidth * activeStep,
            behavior: "smooth",
          })
          setScrollPosition(stepWidth * activeStep)
        }
      } else {
        clearInterval(interval)
        setIsProcessing(false)

        // Wait a moment before completing
        setTimeout(() => {
          onProcessComplete()
        }, 1000)
      }
    }, 1200) // Time for each step

    return () => clearInterval(interval)
  }, [activeStep, isProcessing, onProcessComplete])

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-8">
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-6">Processing Document: {fileName}</h2>

      {/* Main Process Image */}
      <div className="relative w-full mb-10">
        <div className="aspect-[16/9] max-w-4xl mx-auto relative">
          <Image
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/DL_IMAGE%5B1%5D-fn269m7gLCnXNuiMfTi15WAJknAYDY.png"
            alt="Document Processing Workflow Diagram"
            fill
            className="object-contain"
            priority
          />

          {/* Highlight active step in the diagram */}
          {activeStep > 0 && activeStep <= processSteps.length && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="absolute top-0 left-0 w-full h-full">
                <div
                  className="absolute transition-all duration-300 border-2 border-[#1E3A8A] rounded-lg"
                  style={{
                    opacity: 0.7,
                    boxShadow: "0 0 0 4px rgba(30, 58, 138, 0.3)",
                    // Position would need to be adjusted based on the actual diagram
                    top: `${20 + (activeStep - 1) * 5}%`,
                    left: `${20 + (activeStep - 1) * 10}%`,
                    width: "100px",
                    height: "80px",
                    transform: "translate(-50%, -50%)",
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Processing Status */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold border-[#1E3A8A]/20 bg-[#1E3A8A]/10 text-[#1E3A8A]">
          {isProcessing ? (
            <>
              <span className="mr-2 h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
              Processing Step {activeStep} of {processSteps.length}
            </>
          ) : (
            <>
              <span className="mr-2 h-2 w-2 rounded-full bg-green-500"></span>
              Processing Complete
            </>
          )}
        </div>
      </div>

      {/* Step Carousel */}
      <div className="relative">
        <h3 className="text-xl font-semibold mb-4">Process Steps</h3>

        {/* Carousel Navigation Buttons */}
        <div className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-4 z-10">
          <button
            onClick={scrollLeft}
            className="bg-white rounded-full p-2 shadow-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 cursor-pointer"
            aria-label="Scroll left"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>
        </div>

        <div className="absolute top-1/2 right-0 -translate-y-1/2 translate-x-4 z-10">
          <button
            onClick={scrollRight}
            className="bg-white rounded-full p-2 shadow-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 cursor-pointer"
            aria-label="Scroll right"
          >
            <ChevronRight className="h-6 w-6" />
          </button>
        </div>

        {/* Carousel Container */}
        <div
          ref={carouselRef}
          className="flex overflow-x-auto scrollbar-hide snap-x snap-mandatory gap-4 pb-6 px-2 h-full"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {processSteps.map((step) => (
          <div key={step.id} className="flex-shrink-0 w-[250px] snap-start">
            <div
              className={`${step.color} rounded-lg shadow-md overflow-hidden border ${step.borderColor} h-full transition-all duration-300 ${
                activeStep === step.id
                  ? "ring-2 ring-[#1E3A8A] transform scale-[1.02] -m-[2px]" // Reduced scale and negative margin
                  : activeStep > step.id
                    ? "opacity-70"
                    : "opacity-50"
              }`}
              style={{ transformOrigin: 'center center' }} // Ensures even scaling
            >
              {/* Rest of your card content remains the same */}
              <div className="relative h-[150px] bg-gray-100">
                <Image src={ step.image || "/placeholder.svg"} alt={step.caption} fill className="object-cover" />
                <div
                  className={`absolute top-2 left-2 ${
                    activeStep >= step.id ? "bg-[#1E3A8A]" : "bg-gray-400"
                  } text-white text-xs font-bold px-2 py-1 rounded-full transition-colors`}
                >
                  Step {step.id}
                </div>
                {activeStep > step.id && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white text-xs font-bold p-1 rounded-full">
                    ✓
                  </div>
                )}
              </div>
              <div className="p-4">
                <h4 className="font-bold text-lg mb-1">{step.caption}</h4>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
            </div>
          </div>
          ))}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-8 max-w-2xl mx-auto">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden" >
          <div
            className="h-full bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] transition-all duration-500"
            style={{ width: `${(activeStep / processSteps.length) * 100}%` }}
          ></div>
        </div>
        <div className="mt-2 text-sm text-gray-500 text-center">
          {isProcessing ? (
            <>Processing your document... {Math.round((activeStep / processSteps.length) * 100)}%</>
          ) : (
            <>Processing complete! Redirecting to results...</>
          )}
        </div>
      </div>
    </div>
  )
}
