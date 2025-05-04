import { Avatar } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
}

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex items-start gap-4 max-w-3xl", isUser ? "ml-auto" : "mr-auto")}>
      <Avatar
        className={cn("h-8 w-8", isUser ? "order-2" : "")}
        fallback={isUser ? "U" : "AI"}
        size={32}
        src={"/placeholder.svg?height=32&width=32"}
        alt={isUser ? "User" : "AI Assistant"}
      />
      <div
        className={cn(
          "rounded-lg px-4 py-3 max-w-[85%]",
          isUser ? "bg-[#1E3A8A] text-white" : "bg-gray-100 text-gray-800 border border-gray-200",
        )}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{isUser ? "You" : "AI Assistant"}</span>
            <span className="text-xs opacity-70">{formatTime(message.timestamp)}</span>
          </div>
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  }).format(date)
}
