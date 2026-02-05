import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ConfettiPiece {
  id: number;
  x: number;
  color: string;
  delay: number;
  rotation: number;
}

interface ConfettiProps {
  trigger: boolean;
  duration?: number;
  playSound?: boolean;
  intensity?: 'normal' | 'celebration';
}

const colors = [
  'hsl(88, 50%, 45%)',   // Primary green
  'hsl(45, 93%, 47%)',   // Gold
  'hsl(195, 100%, 50%)', // Kid blue
  'hsl(280, 65%, 60%)',  // Kid purple
  'hsl(340, 82%, 65%)',  // Kid pink
  'hsl(142, 71%, 45%)',  // Success green
];

// Play celebration sound using Web Audio API
function playCheerSound(isCelebration: boolean = false) {
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Create a fun "ding" celebration sound
    const playTone = (frequency: number, startTime: number, duration: number, volume: number = 0.3) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(volume, audioContext.currentTime + startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + startTime + duration);
      
      oscillator.start(audioContext.currentTime + startTime);
      oscillator.stop(audioContext.currentTime + startTime + duration);
    };
    
    if (isCelebration) {
      // Play a longer, more exciting celebration fanfare
      playTone(523.25, 0, 0.15, 0.4);      // C5
      playTone(659.25, 0.1, 0.15, 0.4);    // E5
      playTone(783.99, 0.2, 0.15, 0.4);    // G5
      playTone(1046.50, 0.3, 0.3, 0.5);    // C6 (held longer)
      playTone(1174.66, 0.5, 0.15, 0.4);   // D6
      playTone(1318.51, 0.6, 0.15, 0.4);   // E6
      playTone(1567.98, 0.7, 0.4, 0.5);    // G6 (finale)
    } else {
      // Play a quick ascending "success" jingle
      playTone(523.25, 0, 0.15);      // C5
      playTone(659.25, 0.08, 0.15);   // E5
      playTone(783.99, 0.16, 0.2);    // G5
      playTone(1046.50, 0.24, 0.25);  // C6
    }
    
  } catch (e) {
    // Silently fail if audio isn't supported
    console.log('Audio not supported');
  }
}

export function Confetti({ trigger, duration = 2000, playSound = false, intensity = 'normal' }: ConfettiProps) {
  const [pieces, setPieces] = useState<ConfettiPiece[]>([]);

  const triggerConfetti = useCallback(() => {
    const pieceCount = intensity === 'celebration' ? 80 : 30;
    const newPieces: ConfettiPiece[] = Array.from({ length: pieceCount }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: colors[Math.floor(Math.random() * colors.length)],
      delay: Math.random() * (intensity === 'celebration' ? 0.6 : 0.3),
      rotation: Math.random() * 360,
    }));
    setPieces(newPieces);

    // Play celebration sound
    if (playSound) {
      playCheerSound(intensity === 'celebration');
    }

    const timeout = setTimeout(() => {
      setPieces([]);
    }, duration);

    return () => clearTimeout(timeout);
  }, [duration, playSound, intensity]);

  useEffect(() => {
    if (trigger) {
      triggerConfetti();
    }
  }, [trigger, triggerConfetti]);

  return (
    <AnimatePresence>
      {pieces.map((piece) => (
        <motion.div
          key={piece.id}
          initial={{ 
            y: -20, 
            x: `${piece.x}vw`, 
            rotate: 0,
            opacity: 1 
          }}
          animate={{ 
            y: '100vh', 
            rotate: piece.rotation + 720,
            opacity: 0 
          }}
          exit={{ opacity: 0 }}
          transition={{ 
            duration: 2,
            delay: piece.delay,
            ease: 'easeOut'
          }}
          className="fixed top-0 z-50 pointer-events-none"
          style={{ left: `${piece.x}%` }}
        >
          <div 
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: piece.color }}
          />
        </motion.div>
      ))}
    </AnimatePresence>
  );
}
