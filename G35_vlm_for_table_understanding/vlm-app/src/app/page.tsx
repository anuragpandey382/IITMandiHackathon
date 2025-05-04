"use client"
import { Upload } from "@/components/upload"
import { Button } from "@/components/ui/button"
import { ChevronRight, FileText, ImageIcon, Table, Zap } from "lucide-react"
import Link from "next/link"
import { useState } from "react";
export default function Home() {
  const [id, setId] = useState<string | null>("Features");

  return (
    <div className="flex flex-col items-center min-h-screen bg-gradient-to-b from-gray-100 to-gray-50">
      <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
        <div className="flex h-16 w-full items-center justify-between px-4 sm:px-6 lg:px-8 mx-auto">
          {/* Logo - Left aligned */}
          <div className="flex flex-1 items-center justify-start">
            <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] shadow-md">
                <span className="text-sm font-bold text-white">TableEx</span>
              </div>
              <span className="text-lg font-bold bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] bg-clip-text text-transparent sm:text-xl">
                TableEx Document Processor
              </span>
            </Link>
          </div>

          {/* Navigation - Right aligned with slight margin */}
          <div className="flex flex-1 items-center justify-end gap-4">
            <Link href={`#${id}`}>
              <Button
                variant="ghost"
                className="px-3 py-1.5 text-gray-600 hover:bg-gray-50 hover:text-[#1E3A8A] cursor-pointer"
                onClick={() => {
                  id === "Features" ? setId("Process") : id === "Process" ? setId("Top") :setId("Features");
                }}
              >
                {id}
              </Button>
            </Link>
            <Button
              className="px-4 py-1.5 bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] text-white hover:opacity-90 transition-opacity cursor-pointer"
            >
              Get Started
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section id="Top" className="w-full py-12 md:py-12 lg:py-12 xl:py-12 bg-gradient-to-b from-gray-50 to-gray-100 relative overflow-hidden pl-6">
          <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none"></div>
          <div className="container px-4 md:px-6 relative z-10">
            <div className="grid gap-6 lg:grid-cols-[1fr_400px] lg:gap-12 xl:grid-cols-[1fr_600px]">
              <div className="flex flex-col justify-center space-y-4">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-[#1E3A8A] text-white hover:bg-primary/80 w-fit gap-1">
                  <span className="flex h-2 w-2 rounded-full bg-white"></span>
                  Powered by AI
                </div>
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-[#1E3A8A]">
                    Extract Tables From Your Documents
                  </h1>
                  <p className="max-w-[600px] text-gray-600 md:text-xl">
                    Our advanced Visual Language Model analyzes your documents and extracts tables
                    with unparalleled accuracy.
                  </p>
                </div>
                <div className="flex flex-col gap-2 min-[400px]:flex-row">
                  {/* <Button className="bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity h-11 px-8">
                    Try It Now
                  </Button> */}
                  {/* <Link href="https://github.com/TheJayas/DL_Hackathon_G35">
                    <Button variant="outline" className="border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10 h-11 px-8">
                      Learn More
                    </Button>
                  </Link> */}
                </div>
                <div className="flex items-center gap-4 pt-4">
                  {/* <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="h-8 w-8 rounded-full border-2 border-background bg-gray-200 flex items-center justify-center text-xs font-medium"
                      >
                        {String.fromCharCode(64 + i)}
                      </div>
                    ))}
                  </div>
                  <div className="text-sm text-gray-500">
                    Trusted by <span className="font-medium text-[#1E3A8A]">10,000+</span> professionals
                  </div> */}
                </div>
              </div>
              <div className="mx-auto lg:mx-0 w-full max-w-[500px] relative">
                <div className="absolute inset-0 bg-gradient-to-r from-[#1E3A8A]/20 to-[#3B82F6]/20 rounded-xl blur-3xl -z-10 transform -rotate-6"></div>
                <div className="bg-white border rounded-xl shadow-2xl p-6 md:p-8">
                  <div className="space-y-2 mb-6">
                    <h2 className="text-xl font-bold text-[#1E3A8A]">Upload Your Document</h2>
                    <p className="text-sm text-gray-500">PDF, PNG, or JPG files up to 10MB are supported</p>
                  </div>
                  <Upload />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="Features" className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-b from-gray-100 to-gray-50">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-[#1E3A8A] border-[#1E3A8A]/20 bg-[#1E3A8A]/10 hover:bg-[#1E3A8A]/20 w-fit mx-auto">
                  Features
                </div>
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-[#1E3A8A]">
                  Advanced Document Processing
                </h2>
                <p className="max-w-[900px] text-gray-600 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed mx-auto">
                  Our Visual Language Model uses cutting-edge AI to extract and analyze tables from your documents
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col justify-center space-y-4 rounded-xl border bg-gradient-to-b from-white to-gray-50 p-6 shadow-lg transition-all hover:shadow-xl">
                <div className="rounded-full bg-[#1E3A8A]/10 p-3 w-12 h-12 flex items-center justify-center">
                  <Table className="h-6 w-6 text-[#1E3A8A]" />
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">Table Extraction</h3>
                <p className="text-gray-600">
                  Convert complex tables from documents into structured data that can be analyzed and exported.
                </p>
                <div className="pt-2">
                {/* <Link href="https://github.com/TheJayas/DL_Hackathon_G35">
                  <Button variant="link" className="p-0 h-auto text-[#1E3A8A] gap-1 font-medium">
                    Learn more <ChevronRight className="h-4 w-4" />
                  </Button>
                </Link> */}
                </div>
              </div>
              <div className="flex flex-col justify-center space-y-4 rounded-xl border bg-gradient-to-b from-white to-gray-50 p-6 shadow-lg transition-all hover:shadow-xl">
                <div className="rounded-full bg-[#1E3A8A]/10 p-3 w-12 h-12 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-[#1E3A8A]" />
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">PDF Recognition</h3>
                <p className="text-gray-600">
                  Accurately extract and format table content from pdfs, preserving headings, paragraphs, and lists.
                </p>
                <div className="pt-2">
                {/* <Link href="https://github.com/TheJayas/DL_Hackathon_G35">
                  <Button variant="link" className="p-0 h-auto text-[#1E3A8A] gap-1 font-medium">
                    Learn more <ChevronRight className="h-4 w-4" />
                  </Button>
                </Link> */}
                </div>
              </div>
              <div className="flex flex-col justify-center space-y-4 rounded-xl border bg-gradient-to-b from-white to-gray-50 p-6 shadow-lg transition-all hover:shadow-xl">
                <div className="rounded-full bg-[#1E3A8A]/10 p-3 w-12 h-12 flex items-center justify-center">
                  <ImageIcon className="h-6 w-6 text-[#1E3A8A]" />
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">Image Recognition</h3>
                <p className="text-gray-600">
                  Detect and extract tables from images with bounding box visualization, identifying charts, diagrams, and photos.
                </p>
                <div className="pt-2">
                {/* <Link href="https://github.com/TheJayas/DL_Hackathon_G35">
                  <Button variant="link" className="p-0 h-auto text-[#1E3A8A] gap-1 font-medium">
                    Learn more <ChevronRight className="h-4 w-4" />
                  </Button>
                </Link> */}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="Process" className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-b from-gray-50 to-white">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-[#1E3A8A] border-[#1E3A8A]/20 bg-[#1E3A8A]/10 hover:bg-[#1E3A8A]/20 w-fit mx-auto">
                  Process
                </div>
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-[#1E3A8A]">How It Works</h2>
                <p className="max-w-[900px] text-gray-600 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed mx-auto">
                  Our simple three-step process makes document analysis quick and easy
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                    1
                  </div>
                  <div className="absolute top-0 right-0 h-6 w-6 rounded-full bg-green-500 border-4 border-white flex items-center justify-center">
                    <Zap className="h-3 w-3 text-white" />
                  </div>
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">Upload</h3>
                <p className="text-gray-600">
                  Upload your PDF, PNG, or JPG document using our simple drag-and-drop interface
                </p>
              </div>
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                    2
                  </div>
                  <div className="absolute top-0 right-0 h-6 w-6 rounded-full bg-green-500 border-4 border-white flex items-center justify-center">
                    <Zap className="h-3 w-3 text-white" />
                  </div>
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">Process</h3>
                <p className="text-gray-600">Our AI analyzes your document, identifying tables</p>
              </div>
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                    3
                  </div>
                  <div className="absolute top-0 right-0 h-6 w-6 rounded-full bg-green-500 border-4 border-white flex items-center justify-center">
                    <Zap className="h-3 w-3 text-white" />
                  </div>
                </div>
                <h3 className="text-xl font-bold text-[#1E3A8A]">Results</h3>
                <p className="text-gray-600">View and download the extracted content in a clean, organized format</p>
              </div>
            </div>
          </div>
        </section>

        {/* Examples Section */}
        {/* <section id="examples" className="w-full py-12 md:py-24 lg:py-32 bg-white">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-[#1E3A8A] border-[#1E3A8A]/20 bg-[#1E3A8A]/10 hover:bg-[#1E3A8A]/20 w-fit mx-auto">
                  Examples
                </div>
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-[#1E3A8A]">See It In Action</h2>
                <p className="max-w-[900px] text-gray-600 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed mx-auto">
                  Explore examples of how our VLM Document Processor transforms documents
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl gap-6 py-12 lg:grid-cols-2 lg:gap-12">
              <div className="rounded-xl border bg-gradient-to-b from-white to-gray-50 overflow-hidden shadow-lg transition-all hover:shadow-xl">
                <div className="aspect-video bg-gray-100 relative">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-16 w-16 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center">
                      <div className="h-12 w-12 rounded-full bg-[#1E3A8A] flex items-center justify-center">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                          className="w-6 h-6 text-white ml-1"
                        >
                          <path
                            fillRule="evenodd"
                            d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-bold text-[#1E3A8A]">Financial Report Analysis</h3>
                  <p className="mt-2 text-gray-600">
                    See how our VLM extracts tables, charts, and key figures from financial reports.
                  </p>
                  <Button className="mt-4 bg-[#1E3A8A] hover:bg-[#152C6B]">Watch Demo</Button>
                </div>
              </div>
              <div className="rounded-xl border bg-gradient-to-b from-white to-gray-50 overflow-hidden shadow-lg transition-all hover:shadow-xl">
                <div className="aspect-video bg-gray-100 relative">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-16 w-16 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center">
                      <div className="h-12 w-12 rounded-full bg-[#1E3A8A] flex items-center justify-center">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                          className="w-6 h-6 text-white ml-1"
                        >
                          <path
                            fillRule="evenodd"
                            d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-bold text-[#1E3A8A]">Research Paper Processing</h3>
                  <p className="mt-2 text-gray-600">
                    Watch our VLM extract structured data from complex research papers and academic documents.
                  </p>
                  <Button className="mt-4 bg-[#1E3A8A] hover:bg-[#152C6B]">Watch Demo</Button>
                </div>
              </div>
            </div>
          </div>
        </section> */}

        {/* CTA Section */}
        {/* <section className="w-full py-12 md:py-24 lg:py-32 bg-[#1E3A8A]">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-white">
                  Ready to Transform Your Document Workflow?
                </h2>
                <p className="max-w-[600px] text-blue-100 md:text-xl/relaxed mx-auto">
                  Join thousands of professionals who use our VLM Document Processor to save time and extract valuable
                  insights.
                </p>
              </div>
              <div className="flex flex-col gap-2 min-[400px]:flex-row">
                <Button variant="outline"  className=" text-blue-900 hover:bg-white/20 hover:text-white h-11 px-8 bg-white">Get Started Now</Button>
                <Button variant="outline" className="outline-none text-blue-900 hover:bg-white/20 hover:text-white h-11 px-8">
                  Schedule a Demo
                </Button>
              </div>
            </div>
          </div>
        </section> */}
      </main>
      <footer className=" bg-transparent w-full flex justify-center items-center">
        <div className="container px-4 py-8 md:px-6 lg:py-12 items-center justify-center text-3xl">
          <div className="w-full ">
            <div className="space-y-4 justify-center items-center text-center">
              <div className="flex gap-2 justify-center items-center text-center">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-xs">TbEx</span>
                </div>
                <span className="font-bold text-[#1E3A8A]">TableEx Processor</span>
              </div>
              <p className="text-sm text-gray-500">Advanced document processing powered by Visual Language Models.</p>
            </div>
            {/* <div>
              <h3 className="font-medium text-[#1E3A8A] mb-3">Product</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    API
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-[#1E3A8A] mb-3">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Guides
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Support
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-[#1E3A8A] mb-3">Company</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    About
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                    Careers
                  </Link>
                </li>
              </ul>
            </div> */}
          </div>
          <div className="mt-8 border-t pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} TableEx Document Processor. All rights reserved.
            </p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-5 w-5"
                >
                  <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                </svg>
              </Link>
              <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-5 w-5"
                >
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect width="4" height="12" x="2" y="9"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
              </Link>
              <Link href="#" className="text-gray-500 hover:text-[#1E3A8A]">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-5 w-5"
                >
                  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
