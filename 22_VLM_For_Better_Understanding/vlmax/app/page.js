"use client";
import { useState } from 'react';
import Hero from './components/Hero';
import Form from './components/Form';
import Modal from './components/Modal';
import Aurora from '@/ReactBits/Aurora/Aurora';

const HomePage = () => {
  const [modalOpen, setModalOpen] = useState(false)
  const [modalUrl, setModalUrl] = useState('')
  const [modalType, setModalType] = useState('image')

  return (
    <>
      <main className="min-h-screen relative flex flex-col items-center justify-start p-8 ">
        <div className="absolute inset-0 -z-10">
        <Aurora
          colorStops={["#3A29FF", "#FF94B4", "#FF3232"]}
          blend={0.5}
          amplitude={1.0}
          speed={0.5}
        />
        </div>
        <Hero />
        <Form 
            setModalOpen = {setModalOpen}
            setModalUrl = {setModalUrl}
            setModalType = {setModalType}
        />
      </main>

      {modalOpen && (
        <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        url={modalUrl}
        type={modalType}
      />
      )}
    </>
  );
};

export default HomePage;