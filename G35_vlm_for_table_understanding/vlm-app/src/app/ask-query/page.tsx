"use client"

import { useSearchParams } from "next/navigation"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ArrowLeft, CloudCog } from "lucide-react"
import Link from "next/link"
import ChatMessage from "@/components/chat-message"
import { ChatInput } from "@/components/chat-input"
import axios from "axios"
// Define message types
type MessageRole = "user" | "assistant" | "system"

interface Message {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
}

// Sample table data for context
const tableData = {
  headers: ["Product", "Q1 Sales", "Q2 Sales", "Growth"],
  rows: [
    ["Product A", "$245,890", "$312,580", "+27%"],
    ["Product B", "$138,450", "$162,780", "+18%"],
    ["Product C", "$97,350", "$87,620", "-10%"],
    ["Total", "$481,690", "$562,980", "+17%"],
  ],
}

export default function AskQueryPage() {
  const searchParams = useSearchParams()
  const fileName = searchParams.get("fileName") || "document.pdf"
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize with a welcome message
  useEffect(() => {
    const initialMessage: Message = {
      id: "welcome-message",
      role: "assistant",
      content: `Hello! I'm your AI assistant for document "${fileName}". I can help you analyze the tables and data extracted from your document. What would you like to know?`,
      timestamp: new Date(),
    }
    setMessages([initialMessage])
  }, [fileName])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
        console.log("Sending message to AI:", JSON.stringify({query:content}))
        const res = await fetch("http://localhost:5000/ask", {
            headers: {
              "Content-Type": "application/json",
            },
            method: 'POST',
            body: JSON.stringify({query:content}),
          });
          console.log("Response from AI:", res)
          const data = await res.json();
    //   const res = await axios.post("http://localhost:5000/ask", {
    //     query: content,
    //   });
      console.log("Response from AI:", res);
      
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer || "No response from AI.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage])

    } catch (error) {
      console.error("Error generating response:", error)
      const errorMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "Sorry, something went wrong while contacting the AI.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
    setIsLoading(false)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50 shadow-sm">
        <div className="container flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center">
            <Link href={`/results?fileName=${encodeURIComponent(fileName)}`}>
              <Button
                variant="outline"
                size="sm"
                className="gap-1 border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/10 mr-4 cursor-pointer"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Results
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-green-600 to-green-500 flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Document AI Assistant</h1>
                <p className="text-sm text-gray-500">
                  Analyzing: <span className="font-medium">{fileName}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((message : Message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
              <div
                className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              ></div>
              <div
                className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              ></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t bg-white p-4">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
