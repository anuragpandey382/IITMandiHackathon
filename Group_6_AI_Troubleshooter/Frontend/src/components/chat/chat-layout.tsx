// src/components/chat/chat-layout.tsx
'use client';

import React, { useState } from 'react'; // Added useState
import { useEffect } from 'react';
import ChatSidebar from './chat-sidebar';
import ChatContainer from './chat-container'; // Import the new ChatContainer
import { cn } from '@/lib/utils';
import { Conversation, Message } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';

const LOCAL_STORAGE_KEY = 'chat-conversations';

interface ChatLayoutProps {
  defaultLayout: number[] | undefined; // Keep for potential resizable later
  defaultCollapsed?: boolean;
  navCollapsedSize: number;
}

export default function ChatLayout({ defaultLayout = [265, 1000], defaultCollapsed = false, navCollapsedSize }: ChatLayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  type Conversation = {
    id: number;
    title: string;
    messages: Message[];
  };
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  
  const [isLoading, setIsLoading] = useState(false); // State for loading indicator

  // --- Mock Send Message Function (replace with API call later) ---
  const sendMessage = async (text: string) => {
    if (activeChatId === null) return;
  
    setIsLoading(true);
    const userMsg: Message = {
      id: Date.now(),
      text,
      isUser: true,
      timestamp: new Date(),
    };
  
    const botMsg: Message = {
      id: Date.now() + 1,
      text: `You said: ${text}`,
      isUser: false,
      timestamp: new Date(),
    };
  
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeChatId
          ? { ...conv, messages: [...conv.messages, userMsg, botMsg] }
          : conv
      )
    );
  
    setIsLoading(false);
  };
  
  
  const onSelectChat = (id: number) => {
    setActiveChatId(id);
  };
  

   // --- Mock Upload Function ---
   const uploadFile = async (file: File) => {
    console.log("Uploading file:", file.name);
    if (activeChatId === null) return;
  
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate upload delay
  
    const uploadMsg: Message = {
      id: Date.now(),
      text: `You uploaded: ${file.name}`,
      isUser: true,
      timestamp: new Date(),
    };
  
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeChatId
          ? { ...conv, messages: [...conv.messages, uploadMsg] }
          : conv
      )
    );
  
    console.log("Upload complete for:", file.name);
  };
  

  const onNewChat = () => {
    const newChatId = Date.now(); // Using timestamp as ID for simplicity
    const newConversation: Conversation = {
      id: newChatId,
      title: `Conversation ${conversations.length + 1}`,
      messages: [],
    };
    setConversations((prev) => [...prev, newConversation]);
    setActiveChatId(newChatId);
  };
  
  useEffect(() => {
    const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Convert string timestamps back to Date objects
        const restored = parsed.map((conv: Conversation) => ({
          ...conv,
          messages: conv.messages.map((msg: Message) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }));
        setConversations(restored);
        
        // Set active chat to first conversation if exists
        if (restored.length > 0) {
          setActiveChatId(restored[0].id);
        }
      } catch (e) {
        console.error("Failed to parse stored conversations", e);
      }
    }
  }, []);
  
  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  // Get active conversation messages
  const activeConversationMessages = conversations.find(
    (c) => c.id === activeChatId
  )?.messages || [];

  return (
    // Ensure this root div takes full height and width passed from parent
    <div className="flex h-full w-full bg-white dark:bg-gray-900"> {/* Added background */}

      {/* Sidebar */}
      {/* Adjusted width and background */}
      <div className={cn(
          "transition-all duration-300 ease-in-out bg-gray-50 dark:bg-gray-800/50 border-r border-gray-200 dark:border-gray-700",
          isCollapsed ? `w-[${navCollapsedSize}px]` : 'w-[300px]'
      )}>
        <ChatSidebar
          isCollapsed={isCollapsed}
          onNewChat={onNewChat}
          conversations={conversations}
          activeChatId={activeChatId}
          onSelectChat={onSelectChat}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 h-full">
        {activeChatId ? (
          <ChatContainer
            messages={activeConversationMessages}
            onSendMessage={sendMessage}
            onUploadFile={uploadFile}
            isLoading={isLoading}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-3">No conversation selected</h2>
              <p className="text-gray-500 mb-4">Select an existing conversation or start a new one</p>
              <button 
                onClick={onNewChat}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                New Conversation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}