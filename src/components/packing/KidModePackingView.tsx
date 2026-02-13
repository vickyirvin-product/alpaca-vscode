import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Gamepad2, Palette, Send, Target, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Confetti } from '@/components/ui/confetti';
import { PackingItem } from '@/types/packing';
import { useApp } from '@/context/AppContext';
import { KidModeLevel, kidModeLevels } from '@/data/mockData';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { parseActivityItem } from '@/lib/activityIcons';

interface KidModePackingViewProps {
  items: PackingItem[];
  personName: string;
  personId: string;
  kidModeLevel: KidModeLevel;
  setKidModeLevel?: (level: KidModeLevel) => void;
  kidMode?: boolean;
  setKidMode?: (enabled: boolean) => void;
}

export function KidModePackingView({ 
  items, 
  personName, 
  personId,
  kidModeLevel = 'little',
  setKidModeLevel,
  kidMode = true,
  setKidMode,
}: KidModePackingViewProps) {
  const { toggleItemPacked } = useApp();
  const { toast } = useToast();
  const [showConfetti, setShowConfetti] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const visibleItems = items.filter(item => item.visibleToKid);
  const packedCount = visibleItems.filter(i => i.isPacked).length;
  const totalCount = visibleItems.length;
  const progress = totalCount > 0 ? packedCount / totalCount : 0;
  const progressPercent = Math.round(progress * 100);
  const isComplete = progress === 1 && totalCount > 0;
  const unlockedSkin = packedCount >= 3;

  // Get first name only
  const firstName = personName.split(' ')[0];

  const handleItemClick = (itemId: string, currentlyPacked: boolean) => {
    const wasAlmostComplete = packedCount === totalCount - 1;
    
    toggleItemPacked(itemId);
    
    if (!currentlyPacked) {
      // Check if this completes the list
      if (wasAlmostComplete) {
        // Trigger celebration confetti and scroll to top
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 100);
        
        // Scroll to top after a short delay to let the state update
        setTimeout(() => {
          containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
      } else {
        // Regular item pack confetti
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 100);
      }
    }
  };

  const handleSendToParent = () => {
    console.log('Send to parent for approval');
  };

  const handleSelectSkin = () => {
    console.log('Open skin selector');
  };

  // Get style based on kid mode level
  const getLevelStyles = () => {
    switch (kidModeLevel) {
      case 'little':
        return {
          cardSize: 'text-5xl md:text-6xl',
          gridCols: 'grid-cols-2 sm:grid-cols-2 md:grid-cols-3',
          fontSize: 'text-base md:text-lg',
          quantitySize: 'text-lg md:text-xl',
          checkboxSize: 'w-6 h-6 md:w-8 md:h-8',
          checkIconSize: 'w-4 h-4 md:w-5 md:h-5',
        };
      case 'teenager':
        return {
          cardSize: 'text-3xl md:text-4xl',
          gridCols: 'grid-cols-3 sm:grid-cols-4 md:grid-cols-5',
          fontSize: 'text-xs md:text-sm',
          quantitySize: 'text-xs md:text-sm',
          checkboxSize: 'w-4 h-4 md:w-5 md:h-5',
          checkIconSize: 'w-2.5 h-2.5 md:w-3 md:h-3',
        };
      default: // big
        return {
          cardSize: 'text-4xl md:text-5xl',
          gridCols: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4',
          fontSize: 'text-sm md:text-base',
          quantitySize: 'text-base md:text-lg',
          checkboxSize: 'w-5 h-5 md:w-6 md:h-6',
          checkIconSize: 'w-3 h-3 md:w-4 md:h-4',
        };
    }
  };

  const levelStyles = getLevelStyles();

  return (
    <div ref={containerRef} className="bg-gradient-to-br from-primary via-kid-secondary to-kid-accent p-4 relative overflow-hidden rounded-2xl">
      {/* Regular confetti for individual items */}
      <Confetti trigger={showConfetti} playSound />
      
      {/* Celebration confetti for list completion */}
      <Confetti trigger={showCelebration} duration={4000} playSound intensity="celebration" />

      {/* Header Section */}
      <div className="space-y-3 mb-4">
        {/* Title Row */}
        <div className="flex items-center gap-2">
          <Gamepad2 className="w-6 h-6 text-white" />
          <h2 className="text-xl font-bold text-white flex-1">
            {firstName}'s Packing Mission!
          </h2>
        </div>
        
        {/* Kid Mode Toggle & Level Dropdown */}
        {setKidMode && setKidModeLevel && (
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-white">Kid Mode</span>
              <Switch
                checked={kidMode}
                onCheckedChange={setKidMode}
                className="data-[state=checked]:bg-success data-[state=unchecked]:bg-white/30"
              />
            </div>
            {/* Only show level dropdown when Kid Mode is ON */}
            {kidMode && (
              <Select value={kidModeLevel} onValueChange={(v) => setKidModeLevel(v as KidModeLevel)}>
                <SelectTrigger className="w-[130px] h-8 text-sm bg-white/20 border-white/30 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {kidModeLevels.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.emoji} {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        )}

        {/* Mission Progress - Full width bar with counter */}
        <div className="flex items-center gap-3">
          <Target className="w-4 h-4 text-white shrink-0" />
          <div className="h-3 bg-white/30 rounded-full overflow-hidden backdrop-blur-sm flex-1">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full rounded-full bg-gradient-to-r from-vault to-vault-glow"
            />
          </div>
          <span className="text-white font-bold text-sm shrink-0">{packedCount}/{totalCount}</span>
        </div>

        {/* Mission Complete & Send to Parent - At the TOP right below progress */}
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-center gap-2 py-2 px-4 bg-white/20 backdrop-blur-sm rounded-xl">
              <span className="text-xl">🎉</span>
              <div>
                <h3 className="text-base font-bold text-white leading-tight">Mission Complete!</h3>
                <p className="text-xs text-white/80">You're a Packing Pro!</p>
              </div>
            </div>
            
            <Button
              onClick={handleSendToParent}
              size="lg"
              className="w-full py-4 text-base font-bold bg-white text-primary hover:bg-white/90 rounded-xl shadow-lg gap-2"
            >
              <span className="text-lg">👨‍👩‍👧</span>
              Send to Parent for Approval
              <Send className="w-4 h-4" />
            </Button>

            {/* Fun fact about the destination */}
            <div className="p-4 bg-white/20 backdrop-blur-sm rounded-xl">
              <p className="text-sm font-medium text-white/90 leading-relaxed">
                ✨ <span className="font-bold">Fun Fact:</span> Japan has over 5.5 million vending machines – that's one for every 23 people! You can buy everything from drinks to hot meals, toys, and even fresh flowers! 🎰
              </p>
            </div>
          </motion.div>
        )}

        {/* Unlock Skins - Conditional message */}
        <motion.div
          className={cn(
            'flex items-center gap-3 p-3 rounded-xl',
            unlockedSkin 
              ? 'bg-white/30 backdrop-blur-sm' 
              : 'bg-white/20 backdrop-blur-sm'
          )}
        >
          <Palette className="w-5 h-5 text-white" />
          {unlockedSkin ? (
            <>
              <span className="text-sm font-medium text-white flex-1">
                🎉 Congrats! You unlocked custom skins!
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={handleSelectSkin}
                className="h-7 text-xs bg-white/20 border-white/40 text-white hover:bg-white/30"
              >
                Select Skin
              </Button>
            </>
          ) : (
            <span className="text-sm text-white">
              Pack {3 - packedCount} more to unlock custom skins! 🎨
            </span>
          )}
        </motion.div>
      </div>

      {/* Item Grid */}
      <div className={cn("grid gap-3", levelStyles.gridCols)}>
        <AnimatePresence>
          {visibleItems.map((item, index) => (
            <motion.button
              key={item.id}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ delay: index * 0.03 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleItemClick(item.id, item.isPacked)}
              className={cn(
                "aspect-square rounded-2xl p-3 flex flex-col items-center justify-center relative transition-all shadow-lg",
                item.isPacked
                  ? "bg-success/90 border-4 border-success"
                  : "bg-card border-4 border-vault hover:border-vault-glow"
              )}
            >
              {/* Item emoji */}
              <span className={cn(
                "transition-transform mb-1",
                levelStyles.cardSize,
                item.isPacked && "scale-90"
              )}>
                {item.emoji}
              </span>

              {/* Item name - strip asterisk */}
              <p className={cn(
                "font-semibold text-center leading-tight",
                levelStyles.fontSize,
                item.isPacked ? "text-white" : "text-secondary"
              )}>
                {parseActivityItem(item.name).cleanName}
              </p>

              {/* Bottom row: Large Checkbox + Big Quantity */}
              <div className="flex items-center justify-center gap-2 mt-2">
                {/* Large Checkbox */}
                <div className={cn(
                  "rounded-lg border-[3px] flex items-center justify-center transition-all",
                  levelStyles.checkboxSize,
                  item.isPacked 
                    ? "bg-white border-white" 
                    : "bg-white/80 border-vault"
                )}>
                  {item.isPacked && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                    >
                      <Check className={cn("text-success", levelStyles.checkIconSize)} />
                    </motion.div>
                  )}
                </div>
                
                {/* Quantity - always show */}
                <span className={cn(
                  "font-black",
                  levelStyles.quantitySize,
                  item.isPacked ? "text-white" : "text-primary"
                )}>
                  {item.quantity}
                </span>
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
