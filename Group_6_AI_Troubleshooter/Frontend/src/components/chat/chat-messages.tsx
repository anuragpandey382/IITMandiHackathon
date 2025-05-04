// src/components/chat/chat-messages.tsx
'use client';

import React from 'react';
import MessageBubble from './message-bubble';

// Define message type (can be moved to a types file)
export interface Message {
  id: string | number;
  text: string;
  isUser: boolean;
  timestamp: Date;
  imageUrl?: string;
  audioUrl?: string;
}

// Add props interface
interface ChatMessagesProps {
  messages: Message[];
  isThinking?: boolean; // New prop to indicate thinking state
}

// Receive messages as a prop
export default function ChatMessages({ messages, isThinking = false }: ChatMessagesProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    // Scroll to bottom when messages change or when thinking state changes
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  return (
    // Removed padding here, parent div in ChatLayout handles it
    <div className="space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      
      {/* Thinking indicator */}
      {isThinking && (
        <div className="flex items-start gap-3">
          {/* Bot avatar - matching style from message-bubble.tsx */}
          <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center border">
            <span className="text-xs">AI</span>
          </div>
          
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2 max-w-[70%]">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Thinking...</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Dummy div to help scroll to bottom */}
      <div ref={messagesEndRef} />
    </div>
  );
}