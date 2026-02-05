import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Share2, Copy, Check, X, Link2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  itemCount: number;
}

export function ShareDialog({ open, onOpenChange, itemCount }: ShareDialogProps) {
  const [recipientName, setRecipientName] = useState('');
  const [linkGenerated, setLinkGenerated] = useState(false);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const mockLink = 'https://alpaca.app/share/abc123xyz';

  const handleGenerateLink = () => {
    if (!recipientName.trim()) return;
    setLinkGenerated(true);
  };

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(mockLink);
    setCopied(true);
    toast({
      title: "Link copied!",
      description: `Share this with ${recipientName} to delegate packing.`,
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClose = () => {
    onOpenChange(false);
    setTimeout(() => {
      setRecipientName('');
      setLinkGenerated(false);
      setCopied(false);
    }, 200);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-primary" />
            Delegate Items
          </DialogTitle>
          <DialogDescription>
            Create a shareable link for someone to help pack {itemCount} item{itemCount > 1 ? 's' : ''}. 
            No app installation required!
          </DialogDescription>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {!linkGenerated ? (
            <motion.div
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4 py-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium">Who's helping?</label>
                <Input
                  placeholder="e.g., Dad, Grandma, Partner..."
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                />
              </div>
              <Button 
                onClick={handleGenerateLink}
                disabled={!recipientName.trim()}
                className="w-full"
              >
                <Link2 className="w-4 h-4 mr-2" />
                Generate Share Link
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="link"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4 py-4"
            >
              <div className="p-4 bg-muted rounded-xl space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Check className="w-4 h-4 text-primary" />
                  </div>
                  <p className="font-medium">
                    Link ready for {recipientName}!
                  </p>
                </div>
                <div className="flex gap-2">
                  <Input 
                    value={mockLink} 
                    readOnly 
                    className="text-sm bg-background"
                  />
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={handleCopyLink}
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-success" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
              <p className="text-sm text-muted-foreground text-center">
                When {recipientName} checks items off, you'll see them update here in real-time.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
