'use client';
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ChatSidebar from '@/components/chat/chat-sidebar';
import { ChatContainer } from '@/components/chat/chat-container'; // Using named import
import { Conversation } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';

// Rest of your code remains the same
export default function ChatPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);

  // Initialize with a default conversation or load from localStorage
  useEffect(() => {
    const savedConversations = localStorage.getItem('conversations');
    if (savedConversations) {
      try {
        const parsed = JSON.parse(savedConversations);
        // Convert string dates back to Date objects
        const restored = parsed.map((conv: any) => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          messages: conv.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        setConversations(restored);
        
        // Set active chat to the most recent one
        if (restored.length > 0) {
          setActiveChatId(restored[0].id);
        }
      } catch (e) {
        console.error("Error parsing saved conversations:", e);
        createNewChat();
      }
    } else {
      createNewChat();
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  const createNewChat = () => {
    const newId = Date.now(); // Simple ID generation
    const newConversation: Conversation = {
      id: newId,
      title: `New Chat ${conversations.length + 1}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    setConversations([newConversation, ...conversations]);
    setActiveChatId(newId);
  };

  const updateConversation = (updatedConversation: Conversation) => {
    const updatedConversations = conversations.map(conv => 
      conv.id === updatedConversation.id ? updatedConversation : conv
    );
    
    // Sort by most recently updated
    updatedConversations.sort((a, b) => 
      b.updatedAt.getTime() - a.updatedAt.getTime()
    );
    
    setConversations(updatedConversations);
    
    // Update title if it's "New Chat" and we have messages
    if (
      updatedConversation.title.startsWith('New Chat') && 
      updatedConversation.messages.length >= 2
    ) {
      const firstUserMessage = updatedConversation.messages.find(m => m.role === 'user');
      if (firstUserMessage) {
        // Generate title from first user message (truncate if needed)
        const newTitle = firstUserMessage.content.length > 30 
          ? firstUserMessage.content.substring(0, 30) + '...'
          : firstUserMessage.content;
        
        const titleUpdatedConv = { ...updatedConversation, title: newTitle };
        updateConversation(titleUpdatedConv);
      }
    }
  };

  const deleteConversation = (id: number) => {
    const updatedConversations = conversations.filter(conv => conv.id !== id);
    setConversations(updatedConversations);
    if (activeChatId === id) {
      setActiveChatId(updatedConversations.length > 0 ? updatedConversations[0].id : null);
    }
  };

  const activeConversation = conversations.find(conv => conv.id === activeChatId) || null;

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className={`border-r transition-all ${isCollapsed ? 'w-16' : 'w-64'}`}>
        <ChatSidebar 
          isCollapsed={isCollapsed}
          onNewChat={createNewChat}
          conversations={conversations}
          activeChatId={activeChatId}
          onSelectChat={setActiveChatId}
          onDeleteChat={deleteConversation} // Pass delete handler
        />
      </div>
      
      {/* Collapse/Expand button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-4 left-0 transform translate-x-64 z-10"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        {isCollapsed ? <ChevronRightIcon className="h-4 w-4" /> : <ChevronLeftIcon className="h-4 w-4" />}
      </Button>
      
      {/* Chat area */}
      <div className="flex-1">
        {activeConversation ? (
          <ChatContainer 
            activeConversation={activeConversation}
            onUpdateConversation={updateConversation}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">No conversation selected</h2>
              <p className="text-muted-foreground mb-4">Select a conversation or start a new chat</p>
              <Button onClick={createNewChat}>Start new chat</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}