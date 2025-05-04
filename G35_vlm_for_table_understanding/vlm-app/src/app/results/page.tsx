"use client"
import CsvViewer from "@/components/ui/csvviewer"
import { ChevronLeft, ChevronRight, Play, Sheet, Brain, ScanText, FormInput, FileSpreadsheet, Bot } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, Download, FileText, ImageIcon, Table, Check, Copy,MessageSquare } from "lucide-react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useEffect, useState,useRef } from "react"
interface ProcessingData {
  message: string;
  csv_contents: string[];
  detected_table_urls: string[];
  cropped_table_urls:  string[];
  table_structure_urls:  string[];
}
interface DocumentImage {
  id: number;
  src: string;
  alt: string;
  caption: string;
}
export default function ResultsPage() {
  const searchParams = useSearchParams()
  const [csvMessages, setCsvMessages] = useState<string>("");
  const fileName = searchParams.get("fileName") || "document.pdf"
  const [croppedImages, setCroppedImages] = useState<DocumentImage[]>([]);
  const [data, setData] = useState<ProcessingData | null>({cropped_table_urls: [],csv_contents: [],detected_table_urls: [],message: "",table_structure_urls: []});
  const [htmlContent, setHtmlContent] = useState<string>("")
  const [copied, setCopied] = useState(false)
  const structureImagesRef = useRef<HTMLDivElement>(null)
  const [currentStructureImage, setCurrentStructureImage] = useState(0)
  useEffect(() => {
    const storedData = localStorage.getItem("processingResponse");
    console.log("Stored Data:", storedData);
    if (storedData) {
      const response = JSON.parse(storedData);
      setData(response);
      console.log(response);
      console.log("Stored Data:", storedData);
      setCsvMessages(response.csv_contents[0]);
      console.log("CSV Messages:", response.csv_contents[0]);
      setHtmlContent(response.html_contents[0]);
      if(data){
        const images: DocumentImage[] = response.cropped_table_urls.map((url:string, idx:number) => ({
          id: idx + 1,
          src: url,
          alt: `Document Table Structure ${idx + 1}`,
          caption: `Table Structure ${idx + 1}`, 
        }));
        setCroppedImages(images);
        console.log("Document Structure Images:", images);
      }}
    // Simulate loading extracted text
    
  }, [])

  
  const scrollStructureLeft = () => {
    if (structureImagesRef.current) {
      setCurrentStructureImage((prev) => Math.max(0, prev - 1))
    }
  }

  const scrollStructureRight = () => {
    if (structureImagesRef.current) {
      setCurrentStructureImage((prev) => Math.min(croppedImages.length - 1, prev + 1))
    }
  }

  // utils/downloadCSV.ts

 function downloadCSV(csvContent: string, filename = 'data.csv') {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


  return (
    <div className="flex flex-col items-center min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 shadow-sm backdrop-blur-sm">
        <div className="flex h-16 w-full items-center justify-between px-4 sm:px-6 lg:px-8 mx-auto">
          {/* Logo/Link Section */}
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#1E3A8A] to-[#3B82F6] shadow-md">
              <span className="text-sm font-bold text-white">TbEx</span>
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] bg-clip-text text-transparent sm:text-xl">
              TableEx Document Processor
            </span>
          </Link>

          {/* Navigation Buttons */}
          <div className="flex items-center gap-2 sm:gap-4">
            <Link href="/">
              <Button 
                variant="ghost" 
                className="text-gray-600 hover:bg-gray-100 hover:text-[#1E3A8A] px-3 py-1.5 cursor-pointer"
              >
                Dashboard
              </Button>
            </Link>
            {/* <Button 
              className="bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] text-white hover:opacity-90 transition-opacity px-4 py-1.5"
            >
              <span className="hidden sm:inline">New</span> Upload
            </Button> */}
          </div>
        </div>
      </header>
      <main className="flex-1 py-8 md:py-12">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
            <div className="flex items-center">
              <Link href="/">
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1 border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10 cursor-pointer" 
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              </Link>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-[#1E3A8A]">Analysis Results</h1>
                <p className="text-sm text-gray-500">
                  Document: <span className="font-medium">{fileName}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/ask-query?fileName=${encodeURIComponent(fileName)}`}>
                <Button className="gap-2 bg-gradient-to-r from-green-600 to-green-500 hover:opacity-90 transition-opacity cursor-pointer">
                  <MessageSquare className="h-4 w-4" />
                  Ask AI About Document
                </Button>
              </Link>
              {/* <Button variant="outline" className="gap-2 border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10">
                <Copy className="h-4 w-4" />
                Share
              </Button> */}
              {/* <Button className="gap-2 bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity">
                <Download className="h-4 w-4" />
                Download All
              </Button> */}
            </div>
          </div>
          <div className="w-3xl"> 
          <Tabs defaultValue="images" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2 p-1 rounded-xl bg-gray-100/80 backdrop-blur-sm">
              {/* <TabsTrigger
                value="text"
                className="flex items-center gap-2 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-[#1E3A8A] data-[state=active]:to-[#3B82F6] data-[state=active]:text-white transition-all"
              >
                <FileText className="h-4 w-4" />
                Text
              </TabsTrigger> */}
              <TabsTrigger
                value="images"
                className="flex cursor-pointer items-center gap-2 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-[#1E3A8A] data-[state=active]:to-[#3B82F6] data-[state=active]:text-white transition-all"
              >
                <ImageIcon className="h-4 w-4" />
                Cropped Tables
              </TabsTrigger>
              <TabsTrigger
                value="tables"
                className="flex cursor-pointer items-center gap-2 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-[#1E3A8A] data-[state=active]:to-[#3B82F6] data-[state=active]:text-white transition-all"
              >
                <Table className="h-4 w-4" />
                Visualised Tables
              </TabsTrigger>
            </TabsList>

            <TabsContent value="images" className="mt-6">
              <Card className="border-gray-200 shadow-xl overflow-hidden w-full">
                <CardHeader className="bg-gradient-to-r from-[#1E3A8A]/10 to-transparent border-b pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-[#1E3A8A]">Cropped Table Images</CardTitle>
                      <CardDescription>
                        Cropped Tables detected in your document 
                      </CardDescription>
                    </div>
                    {/* <Button size="sm" className="gap-1 bg-[#1E3A8A] hover:bg-[#152C6B]">
                      <Download className="h-4 w-4" />
                      Download All
                    </Button> */}
                  </div>
                </CardHeader>
                <CardContent className="p-6 bg-white">
                  {/* <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="border rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow group">
                      <div className="aspect-video bg-gray-100 relative">
                        <div className="absolute inset-0 flex items-center justify-center">
                          <ImageIcon className="h-12 w-12 text-gray-400" />
                        </div>
                        <div className="absolute inset-0 border-2 border-[#1E3A8A] m-4 rounded-md pointer-events-none opacity-60"></div>
                        <div className="absolute bottom-2 right-2 bg-[#1E3A8A] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          Figure 1
                        </div>
                      </div>
                    </div>
                  </div> */}
                  <div className="relative">
                              {/* Carousel Navigation Buttons */}
                              <div className="absolute top-1/2 left-4 -translate-y-1/2 z-10">
                                {/* <button
                                  onClick={scrollStructureLeft}
                                  className="bg-gray-300 rounded-full p-2 shadow-md hover:bg-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50"
                                  aria-label="Previous image"
                                  disabled={currentStructureImage === 0}
                                >
                                  <ChevronLeft className="h-6 w-6" />
                                </button> */}
                              </div>
                  
                              <div className="absolute top-1/2 right-4 -translate-y-1/2 z-10">
                                {/* <button
                                  onClick={scrollStructureRight}
                                  className="bg-gray-300 rounded-full p-2 shadow-md hover:bg-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50"
                                  aria-label="Next image"
                                  disabled={currentStructureImage === croppedImages.length - 1}
                                >
                                  <ChevronRight className="h-6 w-6" />
                                </button> */}
                              </div>
                  
                              {/* Images */}
                              <div className="overflow-auto rounded-lg">
                                <div
                                  className="flex transition-transform duration-300 ease-in-out"
                                  style={{ transform: `translateX(-${currentStructureImage * 100}%)` }}
                                >
                                  {croppedImages.map((image) => (
                                    <div key={image.id} className="w-full flex-shrink-0">
                                      <div className="relative bg-transparent flex justify-center items-center">
                                        <img src={image.src || "/placeholder.svg"} alt={image.alt}  className="object-contain" />
                                      </div>
                                      <div className="p-4  text-center">
                                        <h4 className="font-medium text-[#1E3A8A]">Detected Table Results</h4>
                                        <p className="text-sm text-gray-500">
                                          {image.id}/{croppedImages.length}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                </CardContent>
                <CardFooter className="bg-gray-50 border-t p-4 flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    <span className="font-medium">{croppedImages.length}</span> images detected
                  </p>
                  {/* <Button className="gap-2 bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity">
                    <Download className="h-4 w-4" />
                    Download All Images
                  </Button> */}
                </CardFooter>
              </Card>
            </TabsContent>

            <TabsContent value="tables" className="mt-6">
              <Card className="border-gray-200 shadow-xl overflow-hidden">
                <CardHeader className="bg-gradient-to-r from-[#1E3A8A]/10 to-transparent border-b pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-[#1E3A8A]">Extracted Tables</CardTitle>
                      <CardDescription>Tables detected and extracted from your document.</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* <Button
                        variant="outline"
                        size="sm"
                        className="gap-1 border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10"
                      >
                        <Copy className="h-4 w-4" />
                        Copy Data
                      </Button> */}
                      <Button size="sm" className="gap-1 bg-[#1E3A8A] hover:bg-[#152C6B] cursor-pointer" onClick={()=>downloadCSV( "Salt Concentration (%),<Trial #1,1 Trial #2,ransmittance (%) Trial #3,Trial #4,: Trial #5\n\nConcentration (%},<Trial #1,Trial #2,Trial #3,Trial #4,( Trial #5\n\n77.23,.74.50 , 64.88, 75.27,54.66,\n\n3:,85.23,92.82,;78.91;,60.71,57.96\n\n6:,88.39,100.05,73.66,66.51,64.54\n\n9,80.71,100.05,68.29,64.91,52.96\n\n12.,82.66 .,117.18,(71.01),( 56.91,46.95\n\n15,72.55,115.40:,65.72,66.03,55.38\n\n")}>
                        <Download className="h-4 w-4" />
                        Export CSV
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-6 bg-white">
                  <div className="border rounded-lg overflow-auto shadow-inner">
                    {/* <table className="w-full caption-bottom text-sm">
                      <thead>
                        <tr className="bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] text-white">
                          <th className="h-12 px-4 text-left align-middle font-medium">Product</th>
                          <th className="h-12 px-4 text-left align-middle font-medium">Q1 Sales</th>
                          <th className="h-12 px-4 text-left align-middle font-medium">Q2 Sales</th>
                          <th className="h-12 px-4 text-left align-middle font-medium">Growth</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b transition-colors hover:bg-gray-100">
                          <td className="p-4 align-middle font-medium">Product A</td>
                          <td className="p-4 align-middle">$245,890</td>
                          <td className="p-4 align-middle">$312,580</td>
                          <td className="p-4 align-middle text-green-600">+27%</td>
                        </tr>
                        <tr className="border-b transition-colors hover:bg-gray-100">
                          <td className="p-4 align-middle font-medium">Product B</td>
                          <td className="p-4 align-middle">$138,450</td>
                          <td className="p-4 align-middle">$162,780</td>
                          <td className="p-4 align-middle text-green-600">+18%</td>
                        </tr>
                        <tr className="border-b transition-colors hover:bg-gray-100">
                          <td className="p-4 align-middle font-medium">Product C</td>
                          <td className="p-4 align-middle">$97,350</td>
                          <td className="p-4 align-middle">$87,620</td>
                          <td className="p-4 align-middle text-red-600">-10%</td>
                        </tr>
                        <tr className="bg-gray-50 font-medium">
                          <td className="p-4 align-middle">Total</td>
                          <td className="p-4 align-middle">$481,690</td>
                          <td className="p-4 align-middle">$562,980</td>
                          <td className="p-4 align-middle text-green-600">+17%</td>
                        </tr>
                      </tbody>
                    </table> */}
                    {/* <CsvViewer csvData={csvMessages} /> */}
                    <div dangerouslySetInnerHTML={{ __html:  htmlContent}} className="overflow-auto"></div>
                  </div>
                  {/* <div className="mt-6 border rounded-lg p-4 bg-gray-50">
                    <h3 className="font-medium text-[#1E3A8A] mb-2">Table Analysis</h3>
                    <p className="text-sm text-gray-600">
                      This table shows quarterly sales data with Product A showing the strongest growth at 27%. Overall
                      sales increased by 17% from Q1 to Q2.
                    </p>
                  </div> */}
                </CardContent>
                <CardFooter className="bg-gray-50 border-t p-4 flex justify-between items-center">
                  {/* <p className="text-sm text-gray-500">
                    <span className="font-medium">1</span>table detected 
                  </p> */}
                  <div className="flex gap-2">
                    {/* <Button variant="outline" className="gap-2 border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10">
                      <Download className="h-4 w-4" />
                      Excel
                    </Button>
                    <Button className="gap-2 bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] hover:opacity-90 transition-opacity">
                      <Download className="h-4 w-4" />
                      CSV
                    </Button> */}
                  </div>
                </CardFooter>
              </Card>
            </TabsContent>
          </Tabs>
          </div>
        </div>
      </main>

      <footer className="bg-white mt-12 w-full">
      <div className="mx-auto flex max-w-7xl flex-col items-center px-4 py-6 md:px-6">
        {/* Divider line */}
        <div className="h-[1px] w-full bg-gray-300"></div>
        
        {/* Content container - now properly centered */}
        <div className="mt-6 flex w-full flex-col items-center justify-between gap-4 sm:flex-row sm:gap-0">
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} TableEx Document Processor. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="text-gray-500 hover:text-[#1E3A8A] cursor-pointer">
              Privacy Policy
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-500 hover:text-[#1E3A8A] cursor-pointer">
              Terms of Service
            </Button>
          </div>
        </div>
      </div>
    </footer>
    </div>
  )
}
