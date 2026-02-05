import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Check, Bookmark } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface SaveListAsTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tripName: string;
  itemCount: number;
}

export function SaveListAsTemplateDialog({
  open,
  onOpenChange,
  tripName,
  itemCount,
}: SaveListAsTemplateDialogProps) {
  const defaultTemplateName = 'International Trip Chilly Weather';
  const [templateName, setTemplateName] = useState(defaultTemplateName);
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setTemplateName('International Trip Chilly Weather');
      setShowSuccess(false);
      setIsSaving(false);
    }
  }, [open]);

  const handleSave = async () => {
    if (!templateName.trim()) return;

    setIsSaving(true);
    
    // Simulate saving - replace with actual save logic when backend is ready
    await new Promise(resolve => setTimeout(resolve, 800));
    
    console.log('Saving entire packing list as template:', templateName.trim());
    
    setIsSaving(false);
    setShowSuccess(true);
    
    // Close dialog after showing success
    setTimeout(() => {
      onOpenChange(false);
    }, 1500);
  };

  const handleClose = () => {
    if (!isSaving) {
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-primary" />
            Save as Template
          </DialogTitle>
          <DialogDescription>
            Save this entire packing list ({itemCount} items) as a reusable template for future trips.
          </DialogDescription>
        </DialogHeader>

        {showSuccess ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-8 gap-3"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center"
            >
              <Check className="w-8 h-8 text-success" />
            </motion.div>
            <p className="text-lg font-medium text-foreground">Template Saved!</p>
            <p className="text-sm text-muted-foreground text-center">
              "{templateName.trim()}" is now available in your templates.
            </p>
          </motion.div>
        ) : (
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="template-name">Template Name</Label>
              <Input
                id="template-name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Enter template name..."
                className="w-full"
                autoFocus
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                onClick={handleClose}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!templateName.trim() || isSaving}
                className="min-w-[100px]"
              >
                {isSaving ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full"
                  />
                ) : (
                  'Save Template'
                )}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
