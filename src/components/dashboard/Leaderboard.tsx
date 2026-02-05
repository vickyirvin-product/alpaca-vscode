import { motion } from 'framer-motion';
import { Medal } from 'lucide-react';
import { Traveler } from '@/types/packing';
import { cn } from '@/lib/utils';

interface LeaderboardProps {
  travelers: Traveler[];
  getPackingProgress: (personId: string) => { packed: number; total: number };
}

export function Leaderboard({ travelers, getPackingProgress }: LeaderboardProps) {
  // Map names for display
  const getDisplayName = (traveler: Traveler) => {
    if (traveler.name.includes('Sarah') || traveler.id === 'mom') return 'Mom';
    if (traveler.name.includes('Mike') || traveler.id === 'dad') return 'Dad';
    return traveler.name.split(' ')[0];
  };

  // Calculate progress for all travelers and sort by percentage
  const leaderboardData = travelers
    .map(t => {
      const progress = getPackingProgress(t.id);
      const percent = progress.total > 0 ? Math.round((progress.packed / progress.total) * 100) : 0;
      return { 
        ...t, 
        percent, 
        isComplete: percent === 100, 
        packed: progress.packed, 
        total: progress.total,
        displayName: getDisplayName(t)
      };
    })
    .sort((a, b) => b.percent - a.percent);

  const leaderId = leaderboardData[0]?.percent > 0 ? leaderboardData[0].id : null;

  return (
    <div className="bg-card rounded-lg border border-border p-2 h-full">
      {/* Header */}
      <div className="mb-2 pb-1.5 border-b border-border">
        <span className="text-xs font-bold text-success uppercase tracking-wide">
          Leaderboard
        </span>
      </div>

      {/* Leaderboard entries - horizontal on mobile, vertical on desktop */}
      <div className="flex sm:flex-col gap-3 sm:gap-2 overflow-x-auto sm:overflow-visible">
        {leaderboardData.map((traveler, index) => {
          const isLeader = traveler.id === leaderId;
          
          return (
            <div key={traveler.id} className="space-y-0.5 min-w-[80px] sm:min-w-0 flex-shrink-0 sm:flex-shrink">
              {/* Name row with medal for leader */}
              <div className="flex items-center justify-between gap-1">
                <div className="flex items-center gap-0.5 min-w-0 flex-1">
                  {isLeader && <Medal className="w-3 h-3 text-vault shrink-0" />}
                  <span className={cn(
                    'text-[11px] font-medium truncate',
                    isLeader ? 'text-vault' : 'text-foreground'
                  )}>
                    {traveler.displayName}
                  </span>
                </div>
                <span className={cn(
                  'text-[10px] font-semibold shrink-0',
                  traveler.isComplete ? 'text-success' : 'text-muted-foreground'
                )}>
                  {traveler.percent}%
                </span>
              </div>
              
              {/* Progress bar */}
              <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
                <motion.div
                  className={cn(
                    'h-full rounded-full',
                    traveler.isComplete ? 'bg-success' : 'bg-primary'
                  )}
                  initial={{ width: 0 }}
                  animate={{ width: `${traveler.percent}%` }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
