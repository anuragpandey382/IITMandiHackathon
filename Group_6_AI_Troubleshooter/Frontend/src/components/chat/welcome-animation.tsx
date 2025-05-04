'use client';

// import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface WelcomeAnimationProps {
  isVisible: boolean;
}

// Particle config for disappearing effect
const generateParticles = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100 - 50,
    y: Math.random() * 100 - 50,
    scale: Math.random() * 0.5 + 0.5,
    rotation: Math.random() * 360
  }));
};

export default function WelcomeAnimation({ isVisible }: WelcomeAnimationProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          className="flex flex-col items-center justify-center h-full px-4 text-center"
          initial={{ opacity: 1 }}
          exit={{ 
            opacity: 0,
            transition: { 
              duration: 0.8,
              when: "afterChildren" 
            }
          }}
        >
          {/* Content container - positioned higher */}
          <div className="flex flex-col items-center relative" style={{ marginTop: "-80px" }}>
            {/* Animation container */}
            <motion.div 
              className="w-80 h-80"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 1.2, delay: 0.1 }}
              exit={{
                scale: 1.2,
                opacity: 0,
                transition: { 
                  duration: 0.7,
                  ease: "easeInOut" 
                }
              }}
            >
              {/* External Lottie animation using iframe */}
              <iframe 
                src="https://lottie.host/embed/5ec8adb8-dabb-4026-83aa-0be266954dbe/36pIxRFwfH.json"
                className="w-full h-full"
                title="Welcome Animation"
                style={{ border: 'none', background: 'transparent' }}
              />
            </motion.div>
            {/* Title and text positioned above the animation */}
            <motion.div className="mb-10 text-center z-10">
              <motion.h1 
                className="text-5xl font-bold mb-3 bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.2 }}
                exit={{
                  opacity: 0,
                  y: -30,
                  filter: "blur(8px)",
                  transition: { duration: 0.5 }
                }}
              >
                MATFix AI
              </motion.h1>
              
              <motion.p
                className="text-xl text-gray-600 dark:text-gray-300 mb-2 max-w-md capitalize"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                exit={{
                  opacity: 0,
                  scale: 0.9,
                  filter: "blur(4px)",
                  transition: { duration: 0.4, delay: 0.1 }
                }}
              >
                Your personal assistant for troubleshooting MATLAB problems
              </motion.p>
              
              <motion.p
                className="text-md text-gray-500 dark:text-gray-400"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                exit={{
                  opacity: 0,
                  scale: 0.9,
                  filter: "blur(4px)",
                  transition: { duration: 0.3, delay: 0.2 }
                }}
              >
                Ask me anything about errors, code or MATLAB concepts
              </motion.p>
            </motion.div>
          

            {/* Floating particles for exit animation */}
            <AnimatePresence>
              {isVisible && (
                <>
                  {generateParticles(40).map((particle) => (
                    <motion.div
                      key={particle.id}
                      className="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-primary/30"
                      initial={{ 
                        x: 0, 
                        y: 0, 
                        opacity: 0,
                        scale: 0
                      }}
                      exit={{ 
                        x: particle.x * 20, 
                        y: particle.y * 20, 
                        opacity: [0, 0.5, 0],
                        scale: particle.scale,
                        rotate: particle.rotation,
                        transition: { 
                          duration: 1.5 + Math.random() * 0.5,
                          ease: "easeOut" 
                        } 
                      }}
                    />
                  ))}
                </>
              )}
            </AnimatePresence>
          </div>
          
          {/* Prompt to start typing */}
          <motion.div
            className="text-sm text-gray-500 dark:text-gray-400 animate-pulse absolute bottom-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 1.2 }}
            exit={{
              opacity: 0,
              y: 10,
              transition: { duration: 0.2 }
            }}
          >
            Type your question to begin...
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}