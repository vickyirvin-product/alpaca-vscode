import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bell, Medal } from 'lucide-react';
import { Traveler } from '@/types/packing';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import { NudgeDialog } from './NudgeDialog';


interface PersonTabBarProps {
  travelers: Traveler[];
  selectedPersonId: string;
  onSelectPerson: (id: string) => void;
  onManage?: () => void;
  getPackingProgress: (personId: string) => {
    packed: number;
    total: number;
  };
  currentUserId?: string;
  overallProgress?: number;
  packedItems?: number;
  totalItems?: number;
}

export function PersonTabBar({
  travelers,
  selectedPersonId,
  onSelectPerson,
  getPackingProgress,
  currentUserId = 'mom',
  overallProgress = 0,
  packedItems = 0,
  totalItems = 0
}: PersonTabBarProps) {
  const [nudgeDialogOpen, setNudgeDialogOpen] = useState(false);

  // Map names for display
  const getDisplayName = (traveler: { name: string; id: string }) => {
    if (traveler.name.includes('Sarah') || traveler.id === 'mom') return 'Mom';
    if (traveler.name.includes('Mike') || traveler.id === 'dad') return 'Dad';
    return traveler.name.split(' ')[0];
  };

  // Calculate progress for all travelers
  const travelersWithProgress = travelers.map(t => {
    const progress = getPackingProgress(t.id);
    const percent = progress.total > 0 ? Math.round(progress.packed / progress.total * 100) : 0;
    return {
      ...t,
      percent,
      isComplete: percent === 100,
      packed: progress.packed,
      total: progress.total
    };
  });

  // Find the leader (highest percent, must be > 0)
  const maxPercent = Math.max(...travelersWithProgress.map(t => t.percent));
  const leaderId = maxPercent > 0 
    ? travelersWithProgress.find(t => t.percent === maxPercent)?.id 
    : null;

  return (
    <div className="space-y-0.5 pt-1">
      {/* Person Avatars Row */}
      <div className="flex items-start gap-2 sm:gap-3 flex-wrap">
        {travelersWithProgress.map(traveler => {
          const isSelected = traveler.id === selectedPersonId;
          const isLeader = traveler.id === leaderId;

          return (
            <motion.div
              key={traveler.id}
              className="relative shrink-0 flex flex-col items-center"
            >
              <motion.button
                onClick={() => onSelectPerson(traveler.id)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={cn(
                  'w-16 h-16 sm:w-[72px] sm:h-[72px] rounded-full flex items-center justify-center transition-all relative overflow-hidden',
                  isSelected
                    ? 'border-primary shadow-md ring-2 ring-primary/30 border-[3px]'
                    : 'border-border hover:border-primary/50 border-2',
                  traveler.isComplete && !isSelected && 'border-success'
                )}
              >
                <span className="text-2xl">{traveler.avatar || '👤'}</span>
              </motion.button>

              {/* 1st place medal on leader */}
              {isLeader && (
                <div className="absolute -top-1 -left-1 w-6 h-6 rounded-full bg-amber-400 flex items-center justify-center shadow-md z-10 border-2 border-background">
                  <Medal className="w-3.5 h-3.5 text-amber-900" />
                </div>
              )}

              {/* Name under avatar */}
              <span
                className={cn(
                  'text-sm mt-1.5 transition-colors',
                  isSelected ? 'text-primary font-semibold' : 'text-muted-foreground'
                )}
              >
                {getDisplayName(traveler)}
              </span>

              {/* Progress bar under name */}
              <div className="w-14 sm:w-16 mt-1">
                <Progress
                  value={traveler.percent}
                  className="h-1 bg-secondary/20 [&>div]:bg-success"
                />
              </div>
            </motion.div>
          );
        })}

        {/* Nudge Link */}
        <button
          onClick={() => setNudgeDialogOpen(true)}
          className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors mt-6 ml-1"
        >
          <Bell className="w-3.5 h-3.5" />
          Nudge
        </button>
      </div>

      {/* Overall Progress Row - left-aligned with first avatar's progress bar */}
      <div className="flex items-center gap-2 mt-4 ml-1">
        <Progress 
          value={overallProgress} 
          className="h-1 flex-1 bg-secondary/20 [&>div]:bg-success" 
        />
        <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
          {packedItems}/{totalItems} ({overallProgress}%)
        </span>
      </div>

      {/* Nudge Dialog */}
      <NudgeDialog
        open={nudgeDialogOpen}
        onOpenChange={setNudgeDialogOpen}
        travelers={travelersWithProgress}
        currentUserId={currentUserId}
        getDisplayName={getDisplayName}
      />
    </div>
  );
}