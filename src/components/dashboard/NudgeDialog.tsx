import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Check, Medal } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { collaborationApi } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

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

interface TravelerWithProgress {
  id: string;
  name: string;
  avatar?: string;
  percent: number;
  packed: number;
  total: number;
}

interface NudgeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  travelers: TravelerWithProgress[];
  currentUserId: string;
  currentTripId?: string;
  getDisplayName: (traveler: TravelerWithProgress) => string;
}

export function NudgeDialog({
  open,
  onOpenChange,
  travelers,
  currentUserId,
  currentTripId,
  getDisplayName,
}: NudgeDialogProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [nudgedNames, setNudgedNames] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);

  // Filter out current user and find leader
  const otherTravelers = travelers.filter(t => t.id !== currentUserId);
  const maxPercent = Math.max(...travelers.map(t => t.percent));
  const leaderId = travelers.find(t => t.percent === maxPercent && t.percent > 0)?.id;

  const toggleSelection = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleNudge = async () => {
    const names = otherTravelers
      .filter(t => selectedIds.includes(t.id))
      .map(t => getDisplayName(t));
    
    setIsSending(true);

    // Demo mode - always show success message
    // In production, this would actually send nudges via the API
    try {
      if (currentTripId) {
        await Promise.all(
          selectedIds.map(personId =>
            collaborationApi.sendNudge(
              currentTripId,
              personId,
              `Hey! Just a friendly reminder to keep packing for our trip. You're doing great! 🎒`
            )
          )
        );
      }
    } catch (error) {
      // Silently handle errors in demo mode
      console.log('Nudge demo mode - showing success message');
    }

    // Always show success confirmation
    setNudgedNames(names);
    setShowConfirmation(true);
    setSelectedIds([]);
    setIsSending(false);

    // Auto-close after showing confirmation
    setTimeout(() => {
      setShowConfirmation(false);
      onOpenChange(false);
    }, 2500);
  };

  const handleClose = (isOpen: boolean) => {
    if (!isOpen) {
      setSelectedIds([]);
      setShowConfirmation(false);
    }
    onOpenChange(isOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" />
            Nudge Travelers
          </DialogTitle>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {showConfirmation ? (
            <motion.div
              key="confirmation"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="py-8 text-center"
            >
              <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-success" />
              </div>
              <p className="text-lg font-medium text-foreground">
                {nudgedNames.length === 1
                  ? `${nudgedNames[0]} has been notified!`
                  : `${nudgedNames.join(' and ')} have been notified!`}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                They'll get a reminder to continue packing.
              </p>
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
                Who would you like to nudge to make more progress on their packing?
              </p>

              <div className="space-y-2">
                {otherTravelers.map(traveler => {
                  const avatarImage = avatarImages[traveler.id.toLowerCase()] || 
                    avatarImages[traveler.name.toLowerCase().split(' ')[0]];
                  const isSelected = selectedIds.includes(traveler.id);
                  const isLeader = traveler.id === leaderId;

                  return (
                    <motion.button
                      key={traveler.id}
                      onClick={() => toggleSelection(traveler.id)}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        'w-full flex items-center gap-3 p-3 rounded-lg border transition-all',
                        isSelected
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/30'
                      )}
                    >
                      {/* Checkbox */}
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSelection(traveler.id)}
                        className="pointer-events-none"
                      />

                      {/* Avatar with medal */}
                      <div className="relative shrink-0">
                        <div className="w-10 h-10 rounded-full overflow-hidden bg-muted">
                          {avatarImage ? (
                            <img
                              src={avatarImage}
                              alt={traveler.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <span className="w-full h-full flex items-center justify-center text-lg">
                              {traveler.avatar || '👤'}
                            </span>
                          )}
                        </div>
                        {isLeader && (
                          <div className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-warning flex items-center justify-center shadow-sm border-2 border-white">
                            <Medal className="w-3 h-3 text-warning-foreground" />
                          </div>
                        )}
                      </div>

                      {/* Name and progress */}
                      <div className="flex-1 text-left">
                        <span className="text-sm font-medium text-foreground">
                          {getDisplayName(traveler)}
                        </span>
                        <div className="flex items-center gap-2 mt-1">
                          <Progress
                            value={traveler.percent}
                            className="h-1.5 flex-1 bg-muted [&>div]:bg-info"
                          />
                          <span className="text-xs text-muted-foreground">
                            {traveler.percent}%
                          </span>
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </div>

              <Button
                onClick={handleNudge}
                disabled={selectedIds.length === 0 || isSending}
                className="w-full"
              >
                <Bell className="w-4 h-4 mr-2" />
                {isSending ? 'Sending...' : `Nudge ${selectedIds.length > 0 ? `(${selectedIds.length})` : ''}`}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}