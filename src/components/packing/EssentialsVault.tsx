import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { PackingItem } from '@/types/packing';
import { PackingItemCard } from './PackingItemCard';
import { cn } from '@/lib/utils';

interface EssentialsVaultProps {
  items: PackingItem[];
  personName: string;
}

export function EssentialsVault({ items, personName }: EssentialsVaultProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const essentialItems = items.filter(item => item.isEssential);
  const unpackedEssentials = essentialItems.filter(item => !item.isPacked);
  
  if (essentialItems.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-2xl border-2 overflow-hidden',
        unpackedEssentials.length > 0
          ? 'border-vault vault-glow'
          : 'border-success bg-success/5'
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full flex items-center gap-3 p-4',
          unpackedEssentials.length > 0
            ? 'gradient-vault'
            : 'bg-success/10'
        )}
      >
        <div className={cn(
          'w-10 h-10 rounded-xl flex items-center justify-center',
          unpackedEssentials.length > 0
            ? 'bg-vault-foreground/20'
            : 'bg-success/20'
        )}>
          <Shield className={cn(
            'w-5 h-5',
            unpackedEssentials.length > 0
              ? 'text-vault-foreground'
              : 'text-success'
          )} />
        </div>
        
        <div className="flex-1 text-left">
          <h3 className={cn(
            'font-semibold',
            unpackedEssentials.length > 0
              ? 'text-vault-foreground'
              : 'text-success'
          )}>
            Essentials Vault
          </h3>
          <p className={cn(
            'text-sm',
            unpackedEssentials.length > 0
              ? 'text-vault-foreground/80'
              : 'text-success/80'
          )}>
            {unpackedEssentials.length === 0 
              ? 'All essentials packed! ✓'
              : `${unpackedEssentials.length} item${unpackedEssentials.length > 1 ? 's' : ''} remaining`
            }
          </p>
        </div>
        
        {isExpanded ? (
          <ChevronUp className={cn(
            'w-5 h-5',
            unpackedEssentials.length > 0 ? 'text-vault-foreground' : 'text-success'
          )} />
        ) : (
          <ChevronDown className={cn(
            'w-5 h-5',
            unpackedEssentials.length > 0 ? 'text-vault-foreground' : 'text-success'
          )} />
        )}
      </button>
      
      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="bg-card"
          >
            <div className="p-4 space-y-2">
              {essentialItems.map(item => (
                <PackingItemCard key={item.id} item={item} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
