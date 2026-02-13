import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ItemCategory } from '@/types/packing';
import { categoryLabels } from '@/data/mockData';
import { cn } from '@/lib/utils';
import { getCategoryIcon } from '@/lib/activityIcons';

interface AddCategoryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (category: ItemCategory) => void;
  existingCategories: ItemCategory[];
}

export function AddCategoryDialog({ isOpen, onClose, onAdd, existingCategories }: AddCategoryDialogProps) {
  const [selectedCategory, setSelectedCategory] = useState<ItemCategory | null>(null);

  const availableCategories = (Object.keys(categoryLabels) as ItemCategory[]).filter(
    cat => !existingCategories.includes(cat)
  );

  const handleAdd = () => {
    if (selectedCategory) {
      onAdd(selectedCategory);
      setSelectedCategory(null);
      onClose();
    }
  };

  const handleClose = () => {
    setSelectedCategory(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Category</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          {availableCategories.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">
              All categories are already in your list!
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {availableCategories.map((category) => {
                // Get category label with fallback for dynamic categories
                const categoryLabel = categoryLabels[category] || {
                  label: category.charAt(0).toUpperCase() + category.slice(1),
                  emoji: getCategoryIcon(category)
                };
                const { label, emoji } = categoryLabel;
                return (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={cn(
                      "flex items-center gap-2 p-3 rounded-lg border-2 transition-colors text-left",
                      selectedCategory === category
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <span className="text-xl">{emoji}</span>
                    <span className="text-sm font-medium">{label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleAdd} 
            disabled={!selectedCategory}
          >
            Add Category
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}