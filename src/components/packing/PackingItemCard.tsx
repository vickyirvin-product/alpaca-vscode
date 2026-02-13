import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Check, AlertCircle, UserPlus, Trash2, Bookmark, MoreVertical, UserCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PackingItem } from '@/types/packing';
import { useApp } from '@/context/AppContext';
import { Confetti } from '@/components/ui/confetti';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { parseActivityItem } from '@/lib/activityIcons';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PackingItemCardProps {
  item: PackingItem;
  isKidMode?: boolean;
  onDelegate?: () => void;
  onDelete?: () => void;
  onSaveToTemplate?: () => void;
}

export function PackingItemCard({ 
  item, 
  isKidMode = false, 
  onDelegate,
  onDelete,
  onSaveToTemplate
}: PackingItemCardProps) {
  const { toggleItemPacked, toggleItemEssential, updatePackingItem } = useApp();
  const [showConfetti, setShowConfetti] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [isEditingQuantity, setIsEditingQuantity] = useState(false);
  const [editedName, setEditedName] = useState(item.name);
  const [editedQuantity, setEditedQuantity] = useState(item.quantity.toString());
  const nameInputRef = useRef<HTMLInputElement>(null);
  const quantityInputRef = useRef<HTMLInputElement>(null);
  
  // Parse activity item to get clean name (remove asterisk)
  const { cleanName } = parseActivityItem(item.name);
  const displayName = cleanName;

  useEffect(() => {
    if (isEditingName && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [isEditingName]);

  useEffect(() => {
    if (isEditingQuantity && quantityInputRef.current) {
      quantityInputRef.current.focus();
      quantityInputRef.current.select();
    }
  }, [isEditingQuantity]);

  const handleTogglePacked = () => {
    if (!item.isPacked && isKidMode) {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 100);
    }
    toggleItemPacked(item.id);
  };

  const handleNameClick = () => {
    if (!item.isPacked) {
      setEditedName(item.name);
      setIsEditingName(true);
    }
  };

  const handleNameSave = async () => {
    if (editedName.trim() && editedName !== item.name) {
      try {
        await updatePackingItem(item.id, { name: editedName.trim() });
      } catch (error) {
        // Error is already handled in AppContext with toast
        setEditedName(item.name); // Revert on error
      }
    }
    setIsEditingName(false);
  };

  const handleNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNameSave();
    } else if (e.key === 'Escape') {
      setEditedName(item.name);
      setIsEditingName(false);
    }
  };

  const handleQuantityClick = () => {
    if (!item.isPacked) {
      setEditedQuantity(item.quantity.toString());
      setIsEditingQuantity(true);
    }
  };

  const handleQuantitySave = async () => {
    const newQuantity = parseInt(editedQuantity, 10);
    if (!isNaN(newQuantity) && newQuantity > 0 && newQuantity !== item.quantity) {
      try {
        await updatePackingItem(item.id, { quantity: newQuantity });
      } catch (error) {
        // Error is already handled in AppContext with toast
        setEditedQuantity(item.quantity.toString()); // Revert on error
      }
    }
    setIsEditingQuantity(false);
  };

  const handleQuantityKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleQuantitySave();
    } else if (e.key === 'Escape') {
      setEditedQuantity(item.quantity.toString());
      setIsEditingQuantity(false);
    }
  };

  // On mobile, opening a Dialog from a Radix DropdownMenu item can immediately close
  // due to the menu's close interaction being treated as an outside click.
  // Deferring the callback avoids that race.
  const defer = (fn?: () => void) => {
    if (!fn) return;
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        fn();
      });
    });
  };

  if (isKidMode) {
    return (
      <>
        <Confetti trigger={showConfetti} />
        <motion.button
          onClick={handleTogglePacked}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={cn(
            'w-full p-6 rounded-2xl border-2 transition-all duration-200',
            item.isPacked
              ? 'bg-success/10 border-success'
              : 'bg-card border-border hover:border-kid-primary'
          )}
        >
          <div className="flex items-center gap-4">
            <span className="text-5xl">{item.emoji}</span>
            <div className="flex-1 text-left">
              <p className={cn(
                'text-2xl font-bold',
                item.isPacked ? 'text-success line-through' : 'text-secondary'
              )}>
                {displayName}
              </p>
              <p className="text-lg text-muted-foreground">
                × {item.quantity}
              </p>
            </div>
            {item.isPacked && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-12 h-12 rounded-full bg-success flex items-center justify-center"
              >
                <Check className="w-8 h-8 text-success-foreground" />
              </motion.div>
            )}
          </div>
        </motion.button>
      </>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        'group flex items-center gap-2 p-2.5 rounded-lg transition-colors',
        item.isPacked 
          ? 'bg-muted/30' 
          : item.delegationInfo
            ? 'bg-info/5 hover:bg-info/10 border border-info/20'
            : 'bg-card hover:bg-muted/50'
      )}
    >
      {/* Delegation indicator */}
      {item.delegationInfo && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="shrink-0 w-5 h-5 rounded-full bg-info/20 flex items-center justify-center">
                <UserCheck className="w-3 h-3 text-info" />
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">
              <p>Delegated by {item.delegationInfo.fromPersonName}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
      
      <Checkbox
        checked={item.isPacked}
        onCheckedChange={() => handleTogglePacked()}
        className="h-5 w-5 shrink-0"
      />
      
      <div className="flex-1 min-w-0">
        {isEditingName ? (
          <div className="flex items-center gap-1">
            <Input
              ref={nameInputRef}
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              onBlur={handleNameSave}
              onKeyDown={handleNameKeyDown}
              className="h-7 text-sm py-0 px-2"
            />
            <Button
              size="icon"
              variant="ghost"
              onClick={handleNameSave}
              className="h-6 w-6 shrink-0"
            >
              <Check className="h-3 w-3" />
            </Button>
          </div>
        ) : (
          <button
            onClick={handleNameClick}
            className={cn(
              'font-medium truncate text-sm text-left w-full hover:text-primary transition-colors',
              item.isPacked && 'line-through text-muted-foreground pointer-events-none'
            )}
          >
            {displayName}
          </button>
        )}
      </div>
      
      {/* Quantity - Editable */}
      {isEditingQuantity ? (
        <div className="flex items-center gap-1">
          <Input
            ref={quantityInputRef}
            type="number"
            min="1"
            value={editedQuantity}
            onChange={(e) => setEditedQuantity(e.target.value)}
            onBlur={handleQuantitySave}
            onKeyDown={handleQuantityKeyDown}
            className="h-6 w-12 text-xs py-0 px-1 text-center"
          />
          <Button
            size="icon"
            variant="ghost"
            onClick={handleQuantitySave}
            className="h-5 w-5 shrink-0"
          >
            <Check className="h-3 w-3" />
          </Button>
        </div>
      ) : (
        <button
          onClick={handleQuantityClick}
          className={cn(
            'text-xs font-semibold text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0 hover:bg-primary/20 hover:text-primary transition-colors',
            item.isPacked && 'pointer-events-none'
          )}
        >
          ×{item.quantity}
        </button>
      )}
      
      {/* Essential indicator - always visible when essential */}
      {item.isEssential && (
        <AlertCircle className="h-4 w-4 text-vault fill-vault/20 shrink-0" />
      )}
      
      {/* 3-dot menu for all actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 shrink-0 text-muted-foreground"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48 bg-card border-border">
          <DropdownMenuItem
            onSelect={() => {
              toggleItemEssential(item.id);
            }}
          >
            <AlertCircle className={cn('h-4 w-4 mr-2', item.isEssential && 'text-vault')} />
            {item.isEssential ? 'Remove from Essentials' : 'Mark as Essential'}
          </DropdownMenuItem>
          <DropdownMenuItem
            onSelect={() => {
              defer(onDelegate);
            }}
          >
            <UserPlus className="h-4 w-4 mr-2 text-primary" />
            Delegate Item
          </DropdownMenuItem>
          <DropdownMenuItem
            onSelect={() => {
              defer(onSaveToTemplate);
            }}
          >
            <Bookmark className="h-4 w-4 mr-2" />
            Save to Template
          </DropdownMenuItem>
          <DropdownMenuItem
            onSelect={() => {
              defer(onDelete);
            }}
            className="text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Item
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </motion.div>
  );
}