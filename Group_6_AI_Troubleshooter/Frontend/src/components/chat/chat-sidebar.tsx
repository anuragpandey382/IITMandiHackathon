// src/components/chat/chat-sidebar.tsx
'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { PlusCircle, Trash2 } from 'lucide-react'; // Icon for New Chat
// import { on } from 'events';
import { Conversation } from '@/types/chat';
// import { deleteConversation } from 'src/page.tsx'; // Import deleteConversation function

interface ChatSidebarProps {
  isCollapsed: boolean;
  onNewChat: () => void;
  conversations: Conversation[];
  activeChatId: number | null;
  onSelectChat: (id: number) => void;
  onDeleteChat: (id: number) => void; // Added delete handler
}

export default function ChatSidebar({
  isCollapsed,
  onNewChat,
  conversations,
  activeChatId,
  onSelectChat,
  onDeleteChat, // Added delete handler
}: ChatSidebarProps) {
  // Dummy history items
  const chatHistory = conversations;

  const handleNewChat = () => {
    console.log("Starting new chat...");
    onNewChat();
  };

  return (
    // Added flex, flex-col, h-full
    <div className={cn("flex flex-col h-full", isCollapsed ? 'p-2' : 'p-4')}>
      {/* Logo */}
      <div className={`mb-4 p-2 border rounded text-center font-bold text-xl ${isCollapsed ? 'w-10 h-10 flex items-center justify-center mx-auto ' : 'w-full'}`}>
        {isCollapsed ? 'M' : 'MATFix AI'}
      </div>

      {/* Chat History Label */}
      {!isCollapsed && <h2 className="text-sm font-semibold mb-2 text-gray-600 dark:text-gray-400 px-2">Chat History</h2>}

      {/* History List */}
      <ScrollArea className="flex-1 -mx-2"> {/* Negative margin to align button edges */}
        <div className={cn("flex flex-col gap-1", isCollapsed ? 'px-0' : 'px-2')}>
          {chatHistory.map((chat,ind) => (
            <div key={chat.id} className="flex flex-row justify-start items-center gap-20">
              <Button
                key={chat.id}
                variant={activeChatId === chat.id ? "secondary" : "ghost"} // Updated variant based on activeChatId
                className={cn(
                  "max-w-40% text-left h-9", // Fixed height
                  isCollapsed ? 'justify-center p-2' : 'justify-start',
                  activeChatId === chat.id && "font-medium" // Added font-medium for active chat
                )}
                title={chat.title} // Tooltip on hover when collapsed
                onClick={() => onSelectChat(chat.id)} // Added onClick handler
              >
                {isCollapsed ? 'Chat '+ind : chat.title} {/* Placeholder icon/text */}
              </Button>
              {!isCollapsed && (
                <div 
                  className="absolute right-2 opacity-0 hover:opacity-100 transition-opacity duration-200" // Added opacity transition
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent triggering the button click
                    onDeleteChat(chat.id);
                  }}
                >
                  <Trash2 
                    className="h-4 w-4 text-gray-400 hover:text-red-500 transition-colors duration-200" 
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* New Chat Button at the bottom */}
      <div className="mt-auto pt-2 md:pt-4">
      <Button
        onClick={handleNewChat}
        className={cn(
          "w-full relative overflow-hidden transition-colors duration-300 border border-transparent",
          isCollapsed ? 'h-10 w-10 p-0' : 'justify-start',
          "hover:bg-background hover:border-primary hover:text-primary hover:cursor-pointer",
        )}
        variant="secondary"
      >
        <PlusCircle className={cn(
          "h-4 w-4 transition-colors duration-300", 
          !isCollapsed && "mr-2",
        )} />
        {!isCollapsed && 'New Chat'}
      </Button>
      </div>
      {/* Optional: Collapse Button */}
      {/* Consider adding a toggle button here */}
    </div>
  );
}