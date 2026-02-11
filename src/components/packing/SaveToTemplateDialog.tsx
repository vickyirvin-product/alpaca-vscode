import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Bookmark, Plus, Info, LogIn } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useApp } from '@/context/AppContext';
import { useNavigate } from 'react-router-dom';

// Dummy templates for prototype
const dummyTemplates = [
  { id: 'must-have', name: 'Must Have Every Trip', emoji: '✅', isSpecial: true },
  { id: 'camping', name: 'Camping', emoji: '🏕️', isSpecial: false },
  { id: 'airplane', name: 'Airplane Trips', emoji: '✈️', isSpecial: false },
  { id: 'phoenix', name: 'Road Trips to Phoenix', emoji: '🚗', isSpecial: false },
];

interface SaveToTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  itemDescription: string;
  itemCount?: number; // For categories
  onSave: (templateIds: string[]) => void;
}

export function SaveToTemplateDialog({
  open,
  onOpenChange,
  itemDescription,
  itemCount,
  onSave,
}: SaveToTemplateDialogProps) {
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<Set<string>>(new Set());
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Mobile guard: when opened from a DropdownMenu, the same tap that closes the menu
  // can be interpreted as a click-outside on the Dialog, immediately closing it.
  // We ignore close requests for a brief window right after opening.
  const openedAtRef = useRef<number>(0);

  useEffect(() => {
    if (open) openedAtRef.current = Date.now();
  }, [open]);

  const toggleTemplate = (templateId: string) => {
    const newSelected = new Set(selectedTemplateIds);
    if (newSelected.has(templateId)) {
      newSelected.delete(templateId);
    } else {
      newSelected.add(templateId);
    }
    setSelectedTemplateIds(newSelected);
  };

  const handleNewTemplateClick = () => {
    setIsCreatingNew(!isCreatingNew);
  };

  const { auth } = useApp();
  const navigate = useNavigate();

  const handleConfirmSave = () => {
    // Check authentication before saving
    if (!auth.isAuthenticated) {
      // Store intent and redirect to login
      sessionStorage.setItem('pending_template_save', JSON.stringify({
        itemDescription,
        itemCount,
        selectedTemplateIds: Array.from(selectedTemplateIds),
        newTemplateName: isCreatingNew ? newTemplateName : null,
      }));
      navigate('/login', { state: { from: window.location.pathname } });
      return;
    }

    const templateIds = Array.from(selectedTemplateIds);
    if (isCreatingNew && newTemplateName.trim()) {
      templateIds.push(`new-${Date.now()}`);
    }
    if (templateIds.length === 0) return;
    
    setIsSaving(true);
    
    // Simulate brief delay for saving
    setTimeout(() => {
      onSave(templateIds);
      setIsSaving(false);
      setShowSuccess(true);
      
      // Close dialog after showing success
      setTimeout(() => {
        setShowSuccess(false);
        setSelectedTemplateIds(new Set());
        setIsCreatingNew(false);
        setNewTemplateName('');
        onOpenChange(false);
      }, 1500);
    }, 300);
  };

  const handleClose = () => {
    if (!isSaving && !showSuccess) {
      setSelectedTemplateIds(new Set());
      setIsCreatingNew(false);
      setNewTemplateName('');
      onOpenChange(false);
    }
  };

  const handleDialogOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      // We don't use a DialogTrigger, but keep this safe/consistent.
      onOpenChange(true);
      return;
    }

    const msSinceOpen = Date.now() - openedAtRef.current;
    if (msSinceOpen < 200) return;

    handleClose();
  };

  const canSave = selectedTemplateIds.size > 0 || (isCreatingNew && newTemplateName.trim());
  const selectedCount = selectedTemplateIds.size + (isCreatingNew && newTemplateName.trim() ? 1 : 0);

  const getSuccessMessage = () => {
    const names: string[] = [];
    selectedTemplateIds.forEach(id => {
      const template = dummyTemplates.find(t => t.id === id);
      if (template) names.push(template.name);
    });
    if (isCreatingNew && newTemplateName.trim()) {
      names.push(newTemplateName.trim());
    }
    if (names.length === 1) return names[0];
    if (names.length === 2) return `${names[0]} and ${names[1]}`;
    return `${names.length} templates`;
  };

  return (
    <Dialog open={open} onOpenChange={handleDialogOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-primary" />
            Save to Template{itemCount ? 's' : ''}
          </DialogTitle>
          <DialogDescription>
            {itemCount ? `${itemCount} items from ${itemDescription}` : itemDescription}
          </DialogDescription>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {showSuccess ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="py-8 flex flex-col items-center gap-4"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center"
              >
                <Check className="w-8 h-8 text-success" />
              </motion.div>
              <div className="text-center">
                <p className="font-semibold text-lg">Saved!</p>
                <p className="text-sm text-muted-foreground">
                  Added to {getSuccessMessage()}
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="selection"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <p className="text-sm text-muted-foreground">
                Select one or more templates:
              </p>

              {/* Template Selection */}
              <div className="space-y-2">
                {dummyTemplates.map(template => {
                  const isSelected = selectedTemplateIds.has(template.id);
                  
                  return (
                    <div key={template.id}>
                      <motion.button
                        onClick={() => toggleTemplate(template.id)}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        className={cn(
                          'w-full flex items-center gap-3 p-3 rounded-xl transition-all border-2 text-left',
                          isSelected 
                            ? 'border-primary bg-primary/10' 
                            : 'border-border hover:border-primary/50 bg-card'
                        )}
                      >
                        <span className="text-xl">{template.emoji}</span>
                        <span className={cn(
                          'flex-1 font-medium',
                          isSelected ? 'text-primary' : 'text-foreground'
                        )}>
                          {template.name}
                        </span>
                        <div className={cn(
                          'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                          isSelected 
                            ? 'border-primary bg-primary' 
                            : 'border-muted-foreground/30'
                        )}>
                          {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
                        </div>
                      </motion.button>
                      
                      {/* Special note for "Must Have Every Trip" */}
                      {template.isSpecial && isSelected && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="flex items-start gap-2 mt-2 p-3 bg-info/10 border border-info/20 rounded-lg text-xs text-info">
                            <Info className="w-4 h-4 shrink-0 mt-0.5" />
                            <p>Items in this template will automatically be added to all current and future trip packing lists.</p>
                          </div>
                        </motion.div>
                      )}
                    </div>
                  );
                })}

                {/* New Template Option */}
                <motion.button
                  onClick={handleNewTemplateClick}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-xl transition-all border-2 border-dashed text-left',
                    isCreatingNew 
                      ? 'border-primary bg-primary/10' 
                      : 'border-border hover:border-primary/50 bg-card'
                  )}
                >
                  <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center">
                    <Plus className="w-4 h-4 text-primary" />
                  </div>
                  <span className={cn(
                    'flex-1 font-medium',
                    isCreatingNew ? 'text-primary' : 'text-muted-foreground'
                  )}>
                    New Template
                  </span>
                </motion.button>

                {/* New Template Name Input */}
                <AnimatePresence>
                  {isCreatingNew && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <Input
                        placeholder="Enter template name..."
                        value={newTemplateName}
                        onChange={(e) => setNewTemplateName(e.target.value)}
                        className="mt-2"
                        autoFocus
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Login prompt for guest users */}
              {!auth.isAuthenticated && (
                <div className="flex items-start gap-2 p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary">
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  <p>Login required to save templates permanently</p>
                </div>
              )}

              {/* Save Button */}
              <Button
                onClick={handleConfirmSave}
                disabled={!canSave || isSaving}
                className="w-full gap-2"
              >
                {isSaving ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full"
                    />
                    Saving...
                  </>
                ) : !auth.isAuthenticated ? (
                  <>
                    <LogIn className="w-4 h-4" />
                    Login to Save
                  </>
                ) : (
                  <>
                    <Bookmark className="w-4 h-4" />
                    Save{selectedCount > 1 ? ` to ${selectedCount} templates` : ''}
                  </>
                )}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}