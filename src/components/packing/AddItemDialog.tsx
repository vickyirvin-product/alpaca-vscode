import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ItemCategory } from '@/types/packing';
import { categoryLabels } from '@/data/mockData';
import { cn } from '@/lib/utils';
import { useApp } from '@/context/AppContext';
import { getCategoryIcon } from '@/lib/activityIcons';

interface AddItemDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (name: string, category: ItemCategory, quantity: number) => void;
  defaultCategory?: ItemCategory;
}

// Simple keyword-based auto-categorization
const categorizeItem = (itemName: string): ItemCategory => {
  const name = itemName.toLowerCase();
  
  // Clothing keywords
  if (/shirt|pants|jeans|shorts|dress|jacket|coat|sweater|socks|underwear|shoes|boots|sandals|hat|cap|scarf|gloves/.test(name)) {
    return 'clothing';
  }
  
  // Electronics
  if (/phone|tablet|laptop|charger|cable|headphones|camera|battery|adapter|kindle|ipad/.test(name)) {
    return 'electronics';
  }
  
  // Toiletries
  if (/toothbrush|toothpaste|shampoo|soap|lotion|sunscreen|deodorant|razor|brush|comb|makeup/.test(name)) {
    return 'toiletries';
  }
  
  // Documents
  if (/passport|visa|ticket|insurance|id|license|reservation|itinerary|document/.test(name)) {
    return 'documents';
  }
  
  // Health
  if (/medicine|medication|pill|vitamin|bandage|first aid|inhaler|prescription|allergy/.test(name)) {
    return 'health';
  }
  
  // Comfort
  if (/pillow|blanket|teddy|lovey|stuffed|toy|comfort/.test(name)) {
    return 'comfort';
  }
  
  // Activities
  if (/book|game|cards|puzzle|coloring|sketch|journal|ball|frisbee/.test(name)) {
    return 'activities';
  }
  
  // Baby
  if (/diaper|formula|bottle|pacifier|stroller|bib|wipes|baby/.test(name)) {
    return 'baby';
  }
  
  return 'misc';
};

// Get emoji for common items
const getItemEmoji = (itemName: string): string => {
  const name = itemName.toLowerCase();
  const emojiMap: Record<string, string> = {
    shirt: '👕', 'tshirt': '👕', 't-shirt': '👕',
    pants: '👖', jeans: '👖',
    shorts: '🩳',
    dress: '👗',
    jacket: '🧥', coat: '🧥',
    sweater: '🧶',
    socks: '🧦',
    shoes: '👟', sneakers: '👟',
    boots: '🥾',
    sandals: '🩴',
    hat: '🧢', cap: '🧢',
    scarf: '🧣',
    phone: '📱',
    laptop: '💻',
    tablet: '📱',
    charger: '🔌',
    headphones: '🎧',
    camera: '📷',
    toothbrush: '🪥',
    sunscreen: '☀️',
    passport: '🛂',
    book: '📚',
    game: '🎮',
    medicine: '💊',
    pillow: '🛏️',
    blanket: '🛏️',
    teddy: '🧸',
    diaper: '🍼',
  };
  
  for (const [keyword, emoji] of Object.entries(emojiMap)) {
    if (name.includes(keyword)) return emoji;
  }
  return '📦';
};

export function AddItemDialog({ isOpen, onClose, onAdd, defaultCategory }: AddItemDialogProps) {
  const [itemName, setItemName] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [suggestedCategory, setSuggestedCategory] = useState<ItemCategory>(defaultCategory || 'misc');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { auth } = useApp();

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (itemName.length > 2) {
      setIsAnalyzing(true);
      // Simulate brief analysis delay for UX
      const timer = setTimeout(() => {
        setSuggestedCategory(categorizeItem(itemName));
        setIsAnalyzing(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [itemName]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (itemName.trim()) {
      onAdd(itemName.trim(), suggestedCategory, quantity);
      setItemName('');
      setQuantity(1);
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="space-y-2"
        >
          {/* Guest mode notice */}
          {!auth.isAuthenticated && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-2 p-2 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary"
            >
              <Info className="w-3 h-3 shrink-0 mt-0.5" />
              <p>Items added in guest mode. Login to save permanently.</p>
            </motion.div>
          )}
          
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <div className="flex items-center gap-2 flex-1">
              <div className="flex-1">
                <Input
                  ref={inputRef}
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter item name..."
                  className="h-9"
                />
              </div>
              
              {/* Quantity input */}
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">×</span>
                <Input
                  type="number"
                  min={1}
                  max={99}
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-14 h-9 text-center"
                />
              </div>
              
              {/* Auto-categorization indicator */}
              {itemName.length > 2 && !isAnalyzing && (
                <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground">
                  <Sparkles className="w-3 h-3 text-primary" />
                  <span className="text-secondary font-medium">
                    {getItemEmoji(itemName)} {categoryLabels[suggestedCategory]?.label || (suggestedCategory.charAt(0).toUpperCase() + suggestedCategory.slice(1))}
                  </span>
                </div>
              )}
              
              <Button
                type="submit"
                size="sm"
                className="h-9"
                disabled={!itemName.trim() || isAnalyzing}
              >
                Add
              </Button>
              
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-9 w-9"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
