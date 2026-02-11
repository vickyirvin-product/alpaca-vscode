import { motion } from 'framer-motion';
import { LogIn, Info, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

interface GuestModeBannerProps {
  onDismiss?: () => void;
}

export function GuestModeBanner({ onDismiss }: GuestModeBannerProps) {
  const navigate = useNavigate();
  const [isDismissed, setIsDismissed] = useState(false);

  const handleLogin = () => {
    // Store current location to return after login
    sessionStorage.setItem('return_after_login', window.location.pathname);
    navigate('/login');
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  if (isDismissed) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-gradient-to-r from-primary/10 via-primary/5 to-accent/10 border-b border-primary/20"
    >
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <Info className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">
                You're in Guest Mode
              </p>
              <p className="text-xs text-muted-foreground">
                Your packing list is saved locally. Login to save it permanently and access it from any device.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              onClick={handleLogin}
              size="sm"
              className="gap-2 shrink-0"
            >
              <LogIn className="w-4 h-4" />
              <span className="hidden sm:inline">Login to Save</span>
              <span className="sm:hidden">Login</span>
            </Button>
            
            <Button
              onClick={handleDismiss}
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}