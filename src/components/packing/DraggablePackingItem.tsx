import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { PackingItem } from '@/types/packing';
import { PackingItemCard } from './PackingItemCard';
import { cn } from '@/lib/utils';
import { GripVertical } from 'lucide-react';

interface DraggablePackingItemProps {
  item: PackingItem;
  isKidMode?: boolean;
  onDelegate?: () => void;
  onDelete?: () => void;
  onSaveToTemplate?: () => void;
}

export function DraggablePackingItem({
  item,
  isKidMode = false,
  onDelegate,
  onDelete,
  onSaveToTemplate,
}: DraggablePackingItemProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: item.id,
    data: {
      item,
      type: 'packing-item',
    },
  });

  const style = transform
    ? {
        transform: CSS.Translate.toString(transform),
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'relative group/drag',
        isDragging && 'opacity-50 z-50'
      )}
    >
      {/* Drag handle - visible on hover */}
      <div
        {...listeners}
        {...attributes}
        className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-5 opacity-0 group-hover/drag:opacity-100 transition-opacity cursor-grab active:cursor-grabbing p-1 touch-none"
      >
        <GripVertical className="w-4 h-4 text-muted-foreground" />
      </div>
      
      <PackingItemCard
        item={item}
        isKidMode={isKidMode}
        onDelegate={onDelegate}
        onDelete={onDelete}
        onSaveToTemplate={onSaveToTemplate}
      />
    </div>
  );
}
