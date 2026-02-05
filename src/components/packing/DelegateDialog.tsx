import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, UserPlus, Send } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Traveler } from '@/types/packing';
import { cn } from '@/lib/utils';

// Avatar images
import emmaAvatar from '@/assets/avatars/emma.jpeg';
import lucasAvatar from '@/assets/avatars/lucas.jpg';
import momAvatar from '@/assets/avatars/mom.jpeg';
import dadAvatar from '@/assets/avatars/dad.jpeg';

const avatarImages: Record<string, string> = {
  'mom': momAvatar,
  'dad': dadAvatar,
  'emma': emmaAvatar,
  'emi': emmaAvatar,
  'lucas': lucasAvatar,
  'cam': lucasAvatar
};

interface DelegateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  travelers: Traveler[];
  currentPersonId: string;
  itemDescription: string; // e.g., "Clothing category" or "T-Shirts"
  itemCount?: number; // For categories
  onDelegate: (toPersonId: string) => void;
}

export function DelegateDialog({
  open,
  onOpenChange,
  travelers,
  currentPersonId,
  itemDescription,
  itemCount,
  onDelegate,
}: DelegateDialogProps) {
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Filter out current person
  const availableTravelers = travelers.filter(t => t.id !== currentPersonId);

  const getDisplayName = (traveler: Traveler) => {
    if (traveler.name.includes('Sarah') || traveler.id === 'mom') return 'Mom';
    if (traveler.name.includes('Mike') || traveler.id === 'dad') return 'Dad';
    return traveler.name.split(' ')[0];
  };

  const handleSelectPerson = (personId: string) => {
    setSelectedPersonId(personId);
  };

  const handleConfirmDelegate = () => {
    if (!selectedPersonId) return;
    
    setIsConfirming(true);
    
    // Simulate brief delay for delegation
    setTimeout(() => {
      onDelegate(selectedPersonId);
      setIsConfirming(false);
      setShowSuccess(true);
      
      // Close dialog after showing success
      setTimeout(() => {
        setShowSuccess(false);
        setSelectedPersonId(null);
        onOpenChange(false);
      }, 1500);
    }, 300);
  };

  const handleClose = () => {
    if (!isConfirming && !showSuccess) {
      setSelectedPersonId(null);
      onOpenChange(false);
    }
  };

  const selectedTraveler = availableTravelers.find(t => t.id === selectedPersonId);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary" />
            Delegate {itemCount ? `${itemCount} items` : 'Item'}
          </DialogTitle>
          <DialogDescription>
            {itemDescription}
          </DialogDescription>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {showSuccess ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="py-8 flex flex-col items-center gap-4"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center"
              >
                <Check className="w-8 h-8 text-success" />
              </motion.div>
              <div className="text-center">
                <p className="font-semibold text-lg">Delegated!</p>
                <p className="text-sm text-muted-foreground">
                  {selectedTraveler && getDisplayName(selectedTraveler)} has been notified
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="selection"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <p className="text-sm text-muted-foreground">
                Who should pack {itemCount ? 'these items' : 'this'}?
              </p>

              {/* Traveler Selection */}
              <div className="grid grid-cols-3 gap-3">
                {availableTravelers.map(traveler => {
                  const isSelected = selectedPersonId === traveler.id;
                  const avatarImage = avatarImages[traveler.id.toLowerCase()] || 
                    avatarImages[traveler.name.toLowerCase().split(' ')[0]];
                  
                  return (
                    <motion.button
                      key={traveler.id}
                      onClick={() => handleSelectPerson(traveler.id)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className={cn(
                        'flex flex-col items-center gap-2 p-3 rounded-xl transition-all border-2',
                        isSelected 
                          ? 'border-primary bg-primary/10 shadow-md' 
                          : 'border-border hover:border-primary/50 bg-card'
                      )}
                    >
                      <div className={cn(
                        'w-14 h-14 rounded-full overflow-hidden border-2 transition-all',
                        isSelected ? 'border-primary' : 'border-transparent'
                      )}>
                        {avatarImage ? (
                          <img src={avatarImage} alt={traveler.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-muted flex items-center justify-center text-2xl">
                            {traveler.avatar || '👤'}
                          </div>
                        )}
                      </div>
                      <span className={cn(
                        'text-sm font-medium',
                        isSelected ? 'text-primary' : 'text-foreground'
                      )}>
                        {getDisplayName(traveler)}
                      </span>
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-primary flex items-center justify-center"
                        >
                          <Check className="w-3 h-3 text-primary-foreground" />
                        </motion.div>
                      )}
                    </motion.button>
                  );
                })}
              </div>

              {/* Delegate Button */}
              <Button
                onClick={handleConfirmDelegate}
                disabled={!selectedPersonId || isConfirming}
                className="w-full gap-2"
              >
                {isConfirming ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full"
                    />
                    Delegating...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Delegate to {selectedTraveler ? getDisplayName(selectedTraveler) : '...'}
                  </>
                )}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
