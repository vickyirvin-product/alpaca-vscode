import { useDroppable } from '@dnd-kit/core';
import { ItemCategory } from '@/types/packing';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface DroppableCategoryProps {
  category: ItemCategory;
  children: ReactNode;
  isOver?: boolean;
}

export function DroppableCategory({ category, children }: DroppableCategoryProps) {
  const { isOver, setNodeRef } = useDroppable({
    id: `category-${category}`,
    data: {
      category,
      type: 'category',
    },
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'transition-all duration-200 rounded-lg',
        isOver && 'ring-2 ring-primary ring-offset-2 bg-primary/5'
      )}
    >
      {children}
    </div>
  );
}
