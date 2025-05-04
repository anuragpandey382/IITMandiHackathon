"use client";
import React, { useState, useEffect, useRef } from 'react';
import { FaArrowUp } from "react-icons/fa";
import { FaRegStopCircle } from "react-icons/fa";

import axios from 'axios';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [visible, setVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [icon, setIcon] = useState(<FaArrowUp />);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (isLoading) {
      setIcon(<FaRegStopCircle />);
    } 
    else {
      setIcon(<FaArrowUp />);
    }
  }, [isLoading]);

  const simulateBackendReply = (text) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { text, timestamp, isUser: false }]);
  };

  async function handlePost(message) {
    try {
      const response = await axios.post('http://localhost:4000/ask', {
        question: message
      });
      return response.data;
    } catch (error) {
      console.error('Error posting message:', error);
      return { answer: "Sorry, I couldn't connect to the server. Please try again later." };
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;
    setIsLoading(true);
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { text: newMessage.trim(), timestamp, isUser: true }]);
    const question = newMessage.trim();
    setNewMessage('');
    const json = await handlePost(question);
    simulateBackendReply(json.answer);
    setIsLoading(false);
  };

  return (
    <div
      className={`transition-all duration-700 ease-out ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
      }`}
    >
      <div className="w-2xl h-2xl bg-zinc-900 rounded-lg shadow-md p-6 flex flex-col">
        {messages.length > 0 ? (
          <div
            className="flex-grow overflow-y-auto mb-2 border border-gray-700 rounded p-2 hide-scrollbar"
            style={{ maxHeight: '300px' }}
          >
            {messages.map(({ text, timestamp, isUser }, index) => (
              <div
                key={index}
                className={`flex mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div className="rounded-lg px-3 py-2 max-w-xs bg-gray-800 text-white shadow relative">
                  <div>{text}</div>
                  <div className="text-xs text-gray-400 mt-1 text-right">
                    {timestamp}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="flex-grow flex items-center justify-center text-gray-500">
            No messages yet. Start the conversation!
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="flex-grow rounded-l p-2 border border-gray-600 focus:outline-none text-sm"
            placeholder="Type a message..."
          />
          <button
            type="submit"
            className="cursor:pointer bg-blue-600 text-white px-4 py-2 rounded-r disabled:bg-gray-600 disabled:cursor-default hover:bg-indigo-500 transition-colors"
            disabled={newMessage.trim() === ''}
          >
            {icon}
          </button>
        </form>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none; /* IE, Edge */
          scrollbar-width: none; /* Firefox */
        }
      `}</style>
    </div>
  );
};

export default ChatWindow;