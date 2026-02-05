import { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, FolderPlus, Gamepad2, Filter, PackageOpen, X, ClipboardList, UserCheck, Users } from 'lucide-react';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { PackingItem, ItemCategory } from '@/types/packing';
import { PackingItemCard } from './PackingItemCard';
import { DraggablePackingItem } from './DraggablePackingItem';
import { DroppableCategory } from './DroppableCategory';
import { CategoryHeader } from './CategoryHeader';
import { AddItemDialog } from './AddItemDialog';
import { AddCategoryDialog } from './AddCategoryDialog';
import { SaveToTemplateDialog } from './SaveToTemplateDialog';
import { DelegateDialog } from './DelegateDialog';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { KidModeLevel, kidModeLevels, categoryLabels } from '@/data/mockData';
import { useApp } from '@/context/AppContext';
import { cn } from '@/lib/utils';

// Animation for items being delegated (swoosh out)
const swooshOutVariants = {
  initial: { opacity: 1, x: 0, scale: 1 },
  exit: { 
    opacity: 0, 
    x: 200, 
    scale: 0.8,
    transition: { 
      duration: 0.4, 
      ease: "easeOut" as const
    }
  }
};

interface CategorySectionProps {
  category: ItemCategory;
  items: PackingItem[];
  isKidMode?: boolean;
  personId: string;
  personName: string;
  onDelegateCategory: (category: ItemCategory) => void;
  onDelegateItem: (itemId: string) => void;
  onDeleteItem: (itemId: string) => Promise<void>;
  onSaveItemToTemplate: (itemId: string) => void;
  onSaveCategoryToTemplate: (category: ItemCategory) => void;
  delegatingItems: Set<string>;
}

function CategorySection({
  category,
  items,
  isKidMode = false,
  personId,
  personName,
  onDelegateCategory,
  onDelegateItem,
  onDeleteItem,
  onSaveItemToTemplate,
  onSaveCategoryToTemplate,
  delegatingItems,
}: CategorySectionProps) {
  const packedCount = items.filter(i => i.isPacked).length;
  const totalCount = items.length;
  const allPacked = packedCount === totalCount && totalCount > 0;
  
  // Auto-collapse when all items are packed
  const [isExpanded, setIsExpanded] = useState(!allPacked);
  const [showAddItem, setShowAddItem] = useState(false);
  const { addPackingItem } = useApp();
  
  // Auto-collapse when all items become packed
  useEffect(() => {
    if (allPacked) {
      setIsExpanded(false);
    }
  }, [allPacked]);
  
  const handleDelete = () => {
    console.log('Delete category:', category);
  };
  
  const handleAddItem = () => {
    setShowAddItem(true);
  };
  
  const handleAddItemSubmit = async (name: string, suggestedCategory: ItemCategory, quantity: number) => {
    try {
      await addPackingItem({
        personId,
        name,
        emoji: '📦',
        quantity,
        category: suggestedCategory,
        isEssential: false,
      });
    } catch (error) {
      // Error is already handled in AppContext with toast
      console.error('Failed to add item:', error);
    }
  };

  // Check if category is being delegated (all items animating out)
  const isCategoryDelegating = items.length > 0 && items.every(item => delegatingItems.has(item.id));

  return (
    <AnimatePresence mode="popLayout">
      {!isCategoryDelegating && (
        <motion.div 
          key={category}
          layout
          initial={{ opacity: 1 }}
          exit={swooshOutVariants.exit}
          className="space-y-1"
        >
          <CategoryHeader 
            category={category} 
            packedCount={packedCount} 
            totalCount={totalCount} 
            isExpanded={isExpanded} 
            onToggle={() => setIsExpanded(!isExpanded)} 
            onDelegate={() => onDelegateCategory(category)} 
            onDelete={handleDelete} 
            onAddItem={handleAddItem} 
            onSaveToTemplate={() => onSaveCategoryToTemplate(category)}
            personName={personName} 
          />

          <AnimatePresence mode="popLayout">
            {isExpanded && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-0.5 ml-1"
              >
                <AddItemDialog 
                  isOpen={showAddItem} 
                  onClose={() => setShowAddItem(false)} 
                  onAdd={handleAddItemSubmit} 
                  defaultCategory={category} 
                />
                
                <AnimatePresence mode="popLayout">
                  {items.map(item => {
                    const isDelegating = delegatingItems.has(item.id);
                    
                    return (
                      <motion.div
                        key={item.id}
                        layout
                        variants={swooshOutVariants}
                        initial="initial"
                        animate={isDelegating ? "exit" : "initial"}
                        exit="exit"
                      >
                        <DraggablePackingItem
                          item={item}
                          isKidMode={isKidMode}
                          onDelegate={() => onDelegateItem(item.id)}
                          onDelete={() => onDeleteItem(item.id)}
                          onSaveToTemplate={() => onSaveItemToTemplate(item.id)}
                        />
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

interface PersonPackingListProps {
  personId: string;
  personName: string;
  avatar: string;
  items: PackingItem[];
  isKidMode?: boolean;
  isChild?: boolean;
  kidMode?: boolean;
  setKidMode?: (enabled: boolean) => void;
  kidModeLevel?: KidModeLevel;
  setKidModeLevel?: (level: KidModeLevel) => void;
}

export function PersonPackingList({
  personId,
  personName,
  avatar,
  items,
  isKidMode = false,
  isChild = false,
  kidMode = false,
  setKidMode,
  kidModeLevel = 'little',
  setKidModeLevel
}: PersonPackingListProps) {
  const { travelers, delegateItem, getTravelerName, addPackingItem, updatePackingItem, deletePackingItem, moveItemToCategory } = useApp();
  const [activeItem, setActiveItem] = useState<PackingItem | null>(null);
  const [showEssentialsOnly, setShowEssentialsOnly] = useState(false);
  const [showUnpackedOnly, setShowUnpackedOnly] = useState(false);
  const [showDelegatedOnly, setShowDelegatedOnly] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [addCategoryDialogOpen, setAddCategoryDialogOpen] = useState(false);
  const [newlyAddedCategory, setNewlyAddedCategory] = useState<ItemCategory | null>(null);
  const categoryRefs = useRef<Record<string, HTMLDivElement | null>>({});
  
  // Delegation state
  const [delegateDialogOpen, setDelegateDialogOpen] = useState(false);
  const [delegationTarget, setDelegationTarget] = useState<{
    type: 'item' | 'category';
    itemId?: string;
    category?: ItemCategory;
    description: string;
    count?: number;
  } | null>(null);
  const [delegatingItems, setDelegatingItems] = useState<Set<string>>(new Set());

  // Save to template state
  const [saveToTemplateDialogOpen, setSaveToTemplateDialogOpen] = useState(false);
  const [saveToTemplateTarget, setSaveToTemplateTarget] = useState<{
    type: 'item' | 'category';
    itemId?: string;
    category?: ItemCategory;
    description: string;
    count?: number;
  } | null>(null);

  const getDisplayName = () => {
    if (personName.includes('Sarah') || personId === 'mom') return 'Mom';
    if (personName.includes('Mike') || personId === 'dad') return 'Dad';
    return personName.split(' ')[0];
  };

  // Filter items
  const filteredItems = useMemo(() => {
    let result = items;
    if (showEssentialsOnly) {
      result = result.filter(item => item.isEssential);
    }
    if (showUnpackedOnly) {
      result = result.filter(item => !item.isPacked);
    }
    if (showDelegatedOnly) {
      result = result.filter(item => item.delegationInfo);
    }
    return result;
  }, [items, showEssentialsOnly, showUnpackedOnly, showDelegatedOnly]);

  const hasActiveFilters = showEssentialsOnly || showUnpackedOnly || showDelegatedOnly;

  const clearFilters = () => {
    setShowEssentialsOnly(false);
    setShowUnpackedOnly(false);
    setShowDelegatedOnly(false);
    setFilterOpen(false);
  };

  // Group items by category
  const itemsByCategory = useMemo(() => {
    const grouped: Partial<Record<ItemCategory, PackingItem[]>> = {};
    filteredItems.forEach(item => {
      if (!grouped[item.category]) {
        grouped[item.category] = [];
      }
      grouped[item.category]!.push(item);
    });
    return grouped;
  }, [filteredItems]);

  const handleAddCategory = () => {
    setAddCategoryDialogOpen(true);
  };

  const handleCategoryAdded = async (category: ItemCategory) => {
    try {
      // Add a placeholder item to create the category
      await addPackingItem({
        personId,
        name: 'New item',
        emoji: categoryLabels[category].emoji,
        quantity: 1,
        category,
        isEssential: false,
      });
      
      setNewlyAddedCategory(category);
      
      // Scroll to the new category after a short delay to allow render
      setTimeout(() => {
        const categoryRef = categoryRefs.current[category];
        if (categoryRef) {
          categoryRef.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        setNewlyAddedCategory(null);
      }, 100);
    } catch (error) {
      // Error is already handled in AppContext with toast
      console.error('Failed to add category:', error);
    }
  };

  // Delegation handlers
  const handleDelegateCategory = (category: ItemCategory) => {
    const categoryItems = items.filter(i => i.category === category);
    const { label } = categoryLabels[category];
    
    setDelegationTarget({
      type: 'category',
      category,
      description: `${getDisplayName()}'s ${label}`,
      count: categoryItems.length,
    });
    setDelegateDialogOpen(true);
  };

  const handleDelegateItem = (itemId: string) => {
    const item = items.find(i => i.id === itemId);
    if (!item) return;
    
    setDelegationTarget({
      type: 'item',
      itemId,
      description: item.name,
    });
    setDelegateDialogOpen(true);
  };

  const handleSaveItemToTemplate = (itemId: string) => {
    const item = items.find(i => i.id === itemId);
    if (!item) return;
    setSaveToTemplateTarget({
      type: 'item',
      itemId,
      description: item.name,
    });
    setSaveToTemplateDialogOpen(true);
  };

  const handleSaveCategoryToTemplate = (category: ItemCategory) => {
    const categoryItems = items.filter(i => i.category === category);
    const { label } = categoryLabels[category];
    setSaveToTemplateTarget({
      type: 'category',
      category,
      description: label,
      count: categoryItems.length,
    });
    setSaveToTemplateDialogOpen(true);
  };

  const handleConfirmSaveToTemplate = (templateIds: string[]) => {
    console.log('Saved', saveToTemplateTarget?.description, 'to templates', templateIds);
    // In a real app, this would save to the templates
  };

  const handleConfirmDelegate = async (toPersonId: string) => {
    if (!delegationTarget) return;

    let itemIdsToDelegate: string[] = [];

    if (delegationTarget.type === 'category' && delegationTarget.category) {
      // Get all item IDs for this category
      itemIdsToDelegate = items
        .filter(i => i.category === delegationTarget.category)
        .map(i => i.id);
    } else if (delegationTarget.type === 'item' && delegationTarget.itemId) {
      itemIdsToDelegate = [delegationTarget.itemId];
    }

    // Start swoosh animation
    setDelegatingItems(new Set(itemIdsToDelegate));

    // After animation completes, actually delegate
    setTimeout(async () => {
      try {
        // Delegate each item individually
        for (const itemId of itemIdsToDelegate) {
          await delegateItem(itemId, toPersonId);
        }
      } catch (error) {
        // Error is already handled in AppContext with toast
        console.error('Failed to delegate items:', error);
      } finally {
        setDelegatingItems(new Set());
        setDelegationTarget(null);
      }
    }, 450);
  };

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const draggedItem = items.find(item => item.id === active.id);
    if (draggedItem) {
      setActiveItem(draggedItem);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveItem(null);

    if (!over) return;

    const overId = over.id.toString();
    if (overId.startsWith('category-')) {
      const newCategory = overId.replace('category-', '') as ItemCategory;
      const itemId = active.id.toString();
      const item = items.find(i => i.id === itemId);
      
      if (item && item.category !== newCategory) {
        moveItemToCategory(itemId, newCategory);
      }
    }
  };

  return (
    <>
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-card rounded-xl border-2 border-success/40 overflow-hidden shadow-sm"
      >
        {/* Header with Person Name */}
        <div className="p-3 border-b-2 border-success/30 bg-success/5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-primary flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-success" />
              {getDisplayName()}'s Packing List
            </h3>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={handleAddCategory} className="h-7 w-7 text-muted-foreground hover:text-primary" title="Add Category">
                <FolderPlus className="w-4 h-4" />
              </Button>

              <Popover open={filterOpen} onOpenChange={setFilterOpen}>
                <PopoverTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className={cn(
                      "h-7 w-7 relative",
                      hasActiveFilters ? "text-primary" : "text-muted-foreground hover:text-primary"
                    )} 
                    title="Filters"
                  >
                    <Filter className="w-4 h-4" />
                    {hasActiveFilters && (
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-primary rounded-full" />
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-56 p-2" align="end">
                  <div className="space-y-1">
                    <button
                      onClick={() => setShowEssentialsOnly(!showEssentialsOnly)}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                        showEssentialsOnly 
                          ? "bg-vault/15 text-vault" 
                          : "hover:bg-muted text-foreground"
                      )}
                    >
                      <AlertCircle className="w-4 h-4" />
                      Essentials Only
                      {showEssentialsOnly && <span className="ml-auto text-xs">✓</span>}
                    </button>
                    <button
                      onClick={() => setShowUnpackedOnly(!showUnpackedOnly)}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                        showUnpackedOnly 
                          ? "bg-info/15 text-info" 
                          : "hover:bg-muted text-foreground"
                      )}
                    >
                      <PackageOpen className="w-4 h-4" />
                      Unpacked Only
                      {showUnpackedOnly && <span className="ml-auto text-xs">✓</span>}
                    </button>
                    <button
                      onClick={() => setShowDelegatedOnly(!showDelegatedOnly)}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                        showDelegatedOnly 
                          ? "bg-info/15 text-info" 
                          : "hover:bg-muted text-foreground"
                      )}
                    >
                      <Users className="w-4 h-4" />
                      Delegated Only
                      {showDelegatedOnly && <span className="ml-auto text-xs">✓</span>}
                    </button>
                    {hasActiveFilters && (
                      <>
                        <div className="border-t border-border my-1" />
                        <button
                          onClick={clearFilters}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted transition-colors"
                        >
                          <X className="w-4 h-4" />
                          Clear filters
                        </button>
                      </>
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Kid Mode Toggle */}
          {isChild && setKidMode && setKidModeLevel && (
            <div className="flex items-center gap-3 py-2 px-3 bg-success/15 border border-success/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Gamepad2 className="w-4 h-4 text-success" />
                <span className="text-sm font-medium text-success">Kid Mode</span>
              </div>
              <Switch checked={kidMode} onCheckedChange={setKidMode} className="data-[state=checked]:bg-success data-[state=unchecked]:bg-muted-foreground/30" />
              {kidMode && (
                <Select value={kidModeLevel} onValueChange={v => setKidModeLevel(v as KidModeLevel)}>
                  <SelectTrigger className="w-[120px] h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {kidModeLevels.map(level => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.emoji} {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          )}
        </div>

        {/* Categories with Drag and Drop */}
        <DndContext 
          sensors={sensors} 
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="p-3 space-y-3">
            {Object.keys(itemsByCategory).length === 0 ? (
              <p className="text-center text-muted-foreground py-8 text-sm">
                {showEssentialsOnly ? 'No essential items marked yet. Use the exclamation icon to mark items as essential.' : 'No items in this list.'}
              </p>
            ) : (
              Object.entries(itemsByCategory).map(([category, categoryItems]) => (
                <DroppableCategory key={category} category={category as ItemCategory}>
                  <div 
                    ref={(el) => { categoryRefs.current[category] = el; }}
                    className={cn(
                      newlyAddedCategory === category && "ring-2 ring-primary ring-offset-2 rounded-lg"
                    )}
                  >
                    <CategorySection
                      category={category as ItemCategory}
                      items={categoryItems}
                      isKidMode={isKidMode}
                      personId={personId}
                      personName={getDisplayName()}
                      onDelegateCategory={handleDelegateCategory}
                      onDelegateItem={handleDelegateItem}
                      onDeleteItem={deletePackingItem}
                      onSaveItemToTemplate={handleSaveItemToTemplate}
                      onSaveCategoryToTemplate={handleSaveCategoryToTemplate}
                      delegatingItems={delegatingItems}
                    />
                  </div>
                </DroppableCategory>
              ))
            )}
          </div>
          
          {/* Drag Overlay */}
          <DragOverlay>
            {activeItem ? (
              <div className="opacity-80 shadow-lg">
                <PackingItemCard item={activeItem} isKidMode={isKidMode} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </motion.div>

      {/* Add Category Dialog */}
      <AddCategoryDialog
        isOpen={addCategoryDialogOpen}
        onClose={() => setAddCategoryDialogOpen(false)}
        onAdd={handleCategoryAdded}
        existingCategories={Object.keys(itemsByCategory) as ItemCategory[]}
      />

      {/* Delegate Dialog */}
      <DelegateDialog
        open={delegateDialogOpen}
        onOpenChange={setDelegateDialogOpen}
        travelers={travelers}
        currentPersonId={personId}
        itemDescription={delegationTarget?.description || ''}
        itemCount={delegationTarget?.count}
        onDelegate={handleConfirmDelegate}
      />

      {/* Save to Template Dialog */}
      <SaveToTemplateDialog
        open={saveToTemplateDialogOpen}
        onOpenChange={setSaveToTemplateDialogOpen}
        itemDescription={saveToTemplateTarget?.description || ''}
        itemCount={saveToTemplateTarget?.count}
        onSave={handleConfirmSaveToTemplate}
      />
    </>
  );
}