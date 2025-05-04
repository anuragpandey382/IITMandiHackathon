import { cn } from "@/lib/utils";
import { Message } from "@/types/chat";
import { Avatar } from "@/components/ui/avatar";
import { BotIcon, LinkIcon, FileTextIcon, UserIcon } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [showReferences, setShowReferences] = useState(false);

  // Safely check for reference links and documents
  const hasReferences =
    (Array.isArray(message.reference_links) &&
      message.reference_links.length > 0) ||
    (Array.isArray(message.relevant_docs) && message.relevant_docs.length > 0);

  // Helper function to safely render document content
  const renderDocContent = (doc: any, index: number) => {
    try {
      // Handle case when doc is null, undefined, or primitive
      if (!doc || typeof doc !== "object") {
        return String(doc || `Document ${index + 1}`);
      }

      // Handle case when doc is an object with title and url
      if (doc.url) {
        return (
          <a
            href={doc.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:underline break-all"
          >
            {doc.title || `Document ${index + 1}`}
          </a>
        );
      }

      // Handle case when doc is an object with title but no url
      if (doc.title) {
        return doc.title;
      }

      // Handle other cases by converting to JSON string
      return `Document ${index + 1}`;
    } catch (error) {
      console.error("Error rendering document:", error);
      return `Document ${index + 1}`;
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 py-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <Avatar className="h-8 w-8">
          <BotIcon className="h-4 w-4" />
        </Avatar>
      )}

      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-lg px-4 py-2.5",
            isUser ? "bg-primary text-primary-foreground" : "bg-muted"
          )}
        >
          {/* Fix: Wrap ReactMarkdown in a div with className instead */}
          <div className="text-sm prose dark:prose-invert prose-sm max-w-none">
            <ReactMarkdown
              components={{
                p: ({ node, ...props }) => (
                  <p className="whitespace-pre-wrap break-words" {...props} />
                ),
                a: ({ node, ...props }) => (
                  <a className="text-blue-600 hover:underline" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc pl-4 my-2" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal pl-4 my-2" {...props} />
                ),
                li: ({ node, ...props }) => <li className="ml-2" {...props} />,
                code: ({ node, inline, ...props }) =>
                  inline ? (
                    <code
                      className="bg-gray-200 dark:bg-gray-700 rounded px-1 py-0.5"
                      {...props}
                    />
                  ) : (
                    <code
                      className="block bg-gray-200 dark:bg-gray-700 rounded p-2 overflow-x-auto"
                      {...props}
                    />
                  ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Image attachment (if any) */}
        {message.imageUrl && (
          <img
            src={message.imageUrl}
            alt="Attached image"
            className="mt-2 max-h-60 rounded-lg"
          />
        )}

        {/* Reference links and documents (only for assistant messages) */}
        {!isUser && hasReferences && (
          <div className="mt-2">
            <button
              onClick={() => setShowReferences(!showReferences)}
              className="flex items-center cursor-pointer gap-1 text-xs text-blue-500 hover:text-blue-700"
            >
              {showReferences ? "Hide" : "Show"} references
              {Array.isArray(message.reference_links) &&
              message.reference_links.length > 0 ? (
                <span className="bg-blue-100 text-blue-800 text-xs font-medium px-1.5 rounded-full dark:bg-blue-900 dark:text-blue-300">
                  {message.reference_links.length}
                </span>
              ) : null}
            </button>

            {showReferences && (
              <div className="mt-2 space-y-2">
                {/* Reference links */}
                {Array.isArray(message.reference_links) &&
                  message.reference_links.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        References:
                      </p>
                      <ul className="space-y-1">
                        {message.reference_links.map((link, index) => (
                          <li key={index} className="flex items-start gap-1">
                            <LinkIcon className="h-3 w-3 mt-0.5 text-gray-500" />
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:underline break-all"
                            >
                              {typeof link === "string"
                                ? link
                                : JSON.stringify(link)}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            )}
          </div>
        )}

        {/* Message timestamp */}
        <span className="text-xs text-muted-foreground mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {isUser && (
        <Avatar className="h-8 w-8">
          <UserIcon className="h-4 w-4" />
        </Avatar>
      )}
    </div>
  );
}
