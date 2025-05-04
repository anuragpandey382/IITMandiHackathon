// src/components/chat/message-bubble.tsx
'use client'
import React from 'react';
import { Message } from './chat-messages'; // Import the interface
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import ReactMarkdown from 'react-markdown'; // Install: npm install react-markdown

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { text, isUser, timestamp, imageUrl, audioUrl } = message;

  return (
    <div className={cn(
      "flex items-start gap-3",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <Avatar className="w-8 h-8 border">
          <AvatarImage src="/bot-avatar.png" alt="Bot" /> {/* Provide a bot avatar */}
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}

      <div className={cn(
        "rounded-lg px-4 py-2 max-w-[70%]",
        isUser
          ? "bg-primary text-primary-foreground"
          : "bg-muted"
      )}>
        {/* Render Markdown Content */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>
            {text}
          </ReactMarkdown>
        </div>

        {/* TODO: Render Image if imageUrl exists */}
        {imageUrl && (
          <img src={imageUrl} alt="Uploaded content" className="mt-2 rounded max-w-xs max-h-xs" />
        )}

        {/* TODO: Render Audio Player if audioUrl exists */}
        {audioUrl && (
          <audio controls src={audioUrl} className="mt-2 w-full max-w-xs">
            Your browser does not support the audio element.
          </audio>
        )}

        <p className="text-xs text-muted-foreground mt-1 text-right opacity-70">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      {isUser && (
        <Avatar className="w-8 h-8 border">
          <AvatarImage src="/user-avatar.png" alt="User" /> {/* Provide a user avatar */}
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}