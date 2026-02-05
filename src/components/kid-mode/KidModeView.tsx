import { useState } from 'react';
import { motion } from 'framer-motion';
import { Printer, ArrowLeft, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PackingItemCard } from '@/components/packing/PackingItemCard';
import { useApp } from '@/context/AppContext';
import { Confetti } from '@/components/ui/confetti';
import { kidModeEmojis } from '@/data/mockData';

interface KidModeViewProps {
  personId: string;
  personName: string;
  onBack: () => void;
}

export function KidModeView({ personId, personName, onBack }: KidModeViewProps) {
  const { getItemsByPerson } = useApp();
  const [celebrateAll, setCelebrateAll] = useState(false);
  
  const items = getItemsByPerson(personId).filter(item => item.visibleToKid);
  const packedCount = items.filter(i => i.isPacked).length;
  const allPacked = packedCount === items.length;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-kid-primary/20 via-kid-secondary/20 to-kid-accent/20 p-4 md:p-8">
      <Confetti trigger={allPacked} duration={3000} />
      
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-secondary"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        
        <Button
          variant="outline"
          onClick={handlePrint}
          className="print:hidden"
        >
          <Printer className="w-5 h-5 mr-2" />
          Print List
        </Button>
      </div>

      {/* Kid-Friendly Header */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="text-center mb-8"
      >
        <div className="text-6xl mb-4">
          {kidModeEmojis[Math.floor(Math.random() * kidModeEmojis.length)]}
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-secondary mb-2">
          {personName}'s Packing List
        </h1>
        <p className="text-xl text-muted-foreground">
          Tap each item when you pack it!
        </p>
        
        {/* Progress Stars */}
        <div className="flex justify-center gap-2 mt-6">
          {items.slice(0, 10).map((item, index) => (
            <motion.span
              key={index}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`text-3xl ${
                index < packedCount ? 'opacity-100' : 'opacity-30'
              }`}
            >
              ⭐
            </motion.span>
          ))}
          {items.length > 10 && (
            <span className="text-xl text-muted-foreground self-center">
              +{items.length - 10} more
            </span>
          )}
        </div>
      </motion.div>

      {/* All Done Celebration */}
      {allPacked && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center py-8 mb-8 bg-success/20 rounded-3xl"
        >
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-success">
            Amazing Job!
          </h2>
          <p className="text-lg text-success/80">
            You packed everything!
          </p>
        </motion.div>
      )}

      {/* Items Grid */}
      <div className="grid gap-4 max-w-2xl mx-auto">
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: index * 0.05 }}
          >
            <PackingItemCard item={item} isKidMode />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
