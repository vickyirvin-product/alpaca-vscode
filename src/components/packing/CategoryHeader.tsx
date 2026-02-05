import { UserPlus, Trash2, Bookmark, Shirt, Bath, Smartphone, FileText, Pill, Heart, Gamepad2, Baby, Package, MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ItemCategory } from '@/types/packing';
import { categoryLabels } from '@/data/mockData';
import { cn } from '@/lib/utils';

// Category icons mapping
const categoryIcons: Record<ItemCategory, React.ComponentType<{ className?: string }>> = {
  clothing: Shirt,
  toiletries: Bath,
  electronics: Smartphone,
  documents: FileText,
  health: Pill,
  comfort: Heart,
  activities: Gamepad2,
  baby: Baby,
  misc: Package,
};

interface CategoryHeaderProps {
  category: ItemCategory;
  packedCount: number;
  totalCount: number;
  isExpanded: boolean;
  onToggle: () => void;
  onDelegate?: () => void;
  onDelete?: () => void;
  onAddItem?: () => void;
  onSaveToTemplate?: () => void;
  personName?: string;
}

export function CategoryHeader({ 
  category, 
  packedCount, 
  totalCount, 
  isExpanded, 
  onToggle,
  onDelegate,
  onDelete,
  onAddItem,
  onSaveToTemplate,
  personName
}: CategoryHeaderProps) {
  const { label } = categoryLabels[category];
  const allPacked = packedCount === totalCount && totalCount > 0;
  const CategoryIcon = categoryIcons[category];

  // Personalize category names for clothing and toiletries
  const getDisplayLabel = () => {
    if ((category === 'clothing' || category === 'toiletries') && personName) {
      return `${personName}'s ${label}`;
    }
    return label;
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

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onToggle}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggle(); }}
      className={cn(
        'w-full flex items-center gap-2 py-2.5 px-3 rounded-lg transition-all cursor-pointer min-w-0',
        'bg-secondary/5 hover:bg-secondary/10',
        allPacked && 'bg-success/10'
      )}
    >
      {/* Category Icon */}
      <CategoryIcon className={cn(
        'w-4 h-4 shrink-0',
        allPacked ? 'text-success' : 'text-info'
      )} />
      
      {/* Category name - bold and left-aligned, with proper truncation */}
      <h4 className={cn(
        'font-bold text-sm uppercase tracking-wide text-left flex-1 min-w-0 truncate',
        allPacked ? 'text-success' : 'text-secondary'
      )}>
        {getDisplayLabel()}
      </h4>
      
      {/* Progress count */}
      <span className={cn(
        'text-xs font-semibold px-1.5 py-0.5 rounded-md shrink-0',
        allPacked
          ? 'bg-success/20 text-success'
          : 'bg-muted text-muted-foreground'
      )}>
        {packedCount}/{totalCount}
      </span>
      
      {/* Action menu - 3 dot menu */}
      <div
        onPointerDown={(e) => e.stopPropagation()}
        onClick={(e) => e.stopPropagation()}
      >
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 text-muted-foreground hover:text-primary"
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48 bg-card border-border">
            <DropdownMenuItem onSelect={() => defer(onDelegate)}>
              <UserPlus className="h-4 w-4 mr-2 text-primary" />
              Delegate Category
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => defer(onSaveToTemplate)}>
              <Bookmark className="h-4 w-4 mr-2" />
              Save to Template
            </DropdownMenuItem>
            <DropdownMenuItem 
              onSelect={() => defer(onDelete)}
              className="text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Category
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}