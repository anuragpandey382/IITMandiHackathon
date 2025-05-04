"use client";
import Hero from '../components/Hero';
import ChatWindow from '../components/ChatWindow';
import Aurora from '@/ReactBits/Aurora/Aurora';

const ChatPage = () => {

  return (
    <main className="min-h-screen relative flex flex-col items-center justify-start p-8 ">
      <div className="absolute inset-0 -z-10">
      <Aurora
        colorStops={["#3A29FF", "#FF94B4", "#FF3232"]}
        blend={0.5}
        amplitude={1.0}
        speed={0.5}
      />
      </div>
      <Hero/>
      <ChatWindow />
    </main>
  );
};

export default ChatPage;