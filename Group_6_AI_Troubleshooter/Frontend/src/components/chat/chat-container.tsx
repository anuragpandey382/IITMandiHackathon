'use client';

import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Conversation, Message } from '@/types/chat';
import { ChatInput } from './chat-input';
import { ChatMessage } from './chat-message';
import { chatService } from '@/services/chat-service';
import WelcomeAnimation from './welcome-animation';

interface ChatContainerProps {
  activeConversation: Conversation;
  onUpdateConversation: (conversation: Conversation) => void;
}

export interface ChatMessageProps {
  message: Message;
}

export function ChatContainer({ activeConversation, onUpdateConversation }: ChatContainerProps) {
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Show welcome animation ONLY when there are no messages
  const showWelcome = activeConversation?.messages?.length === 0;

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConversation?.messages, isLoading]);

  const handleSendMessage = async (content: string, image?: File) => {
    setIsLoading(true);
    
    // Create a user message
    const userMessage: Message = {
      id: uuidv4(),
      content,
      role: 'user',
      timestamp: new Date(),
      imageUrl: image ? URL.createObjectURL(image) : undefined
    };
    
    const updatedMessages = [...activeConversation.messages, userMessage];
    
    // Update conversation with user message immediately
    const updatedConversation = {
      ...activeConversation,
      messages: updatedMessages,
      updatedAt: new Date()
    };
    onUpdateConversation(updatedConversation);

    try {
      // Send message to the API
      const response = await chatService.sendMessage(content, image);
      
      // Create assistant response
      const assistantMessage: Message = {
        id: uuidv4(),
        content: response.message,
        role: 'assistant',
        timestamp: new Date(),
        reference_links: response.reference_links,
        relevant_docs: response.relevant_docs
      };
      
      // Update conversation with assistant response
      const finalConversation = {
        ...activeConversation,
        messages: [...updatedMessages, assistantMessage],
        updatedAt: new Date()
      };
      onUpdateConversation(finalConversation);
      
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Add error message
      const errorMessage: Message = {
        id: uuidv4(),
        content: "Sorry, there was an error processing your message. Please try again.",
        role: 'assistant',
        timestamp: new Date()
      };
      
      const errorConversation = {
        ...activeConversation,
        messages: [...updatedMessages, errorMessage],
        updatedAt: new Date()
      };
      onUpdateConversation(errorConversation);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Use a flex column layout with fixed height
    <div className="flex flex-col h-full">
      {/* Messages area - will take remaining space and be scrollable */}
      <div className="flex-1 overflow-hidden relative">
        <ScrollArea className="h-full p-4">
          <div className="space-y-4 pb-5">
            {activeConversation?.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            
            {/* Thinking indicator */}
            {isLoading && (
              <div className="flex items-start gap-3">
                {/* Bot avatar */}
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
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
        
        {/* Welcome animation overlay */}
        <div className="absolute inset-0 pointer-events-none">
          <WelcomeAnimation isVisible={showWelcome} />
        </div>
      </div>
      
      {/* Input area - fixed at the bottom */}
      <div className="border-t">
        <ChatInput 
          onSendMessage={handleSendMessage} 
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}