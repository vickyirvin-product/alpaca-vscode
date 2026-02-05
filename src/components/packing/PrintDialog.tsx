import { useState } from 'react';
import { Printer, Users } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Traveler } from '@/types/packing';
import { cn } from '@/lib/utils';

interface PrintDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  travelers: Traveler[];
}

export function PrintDialog({ open, onOpenChange, travelers }: PrintDialogProps) {
  const [printAll, setPrintAll] = useState(true);
  const [selectedTravelers, setSelectedTravelers] = useState<string[]>([]);

  const handlePrintAllChange = (checked: boolean) => {
    setPrintAll(checked);
    if (checked) {
      setSelectedTravelers([]);
    }
  };

  const handleTravelerToggle = (travelerId: string) => {
    setPrintAll(false);
    setSelectedTravelers(prev => 
      prev.includes(travelerId)
        ? prev.filter(id => id !== travelerId)
        : [...prev, travelerId]
    );
  };

  const handlePrint = () => {
    // In a real implementation, you'd filter the print content based on selection
    // For now, we'll just trigger the browser print dialog
    console.log('Printing:', printAll ? 'All lists' : selectedTravelers);
    window.print();
    onOpenChange(false);
  };

  const canPrint = printAll || selectedTravelers.length > 0;

  const handleClose = () => {
    onOpenChange(false);
    // Reset state after close
    setTimeout(() => {
      setPrintAll(true);
      setSelectedTravelers([]);
    }, 200);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Printer className="w-5 h-5 text-info" />
            Print Packing Lists
          </DialogTitle>
          <DialogDescription>
            Choose which packing lists you'd like to print.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Print All Option */}
          <div 
            className={cn(
              "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
              printAll 
                ? "border-info bg-info/10" 
                : "border-border hover:border-muted-foreground/50"
            )}
            onClick={() => handlePrintAllChange(true)}
          >
            <Checkbox 
              id="print-all"
              checked={printAll}
              onCheckedChange={handlePrintAllChange}
              className="data-[state=checked]:bg-info data-[state=checked]:border-info"
            />
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-muted-foreground" />
              <Label htmlFor="print-all" className="cursor-pointer font-medium">
                Print All Lists
              </Label>
            </div>
            <span className="ml-auto text-xs text-muted-foreground">
              {travelers.length} {travelers.length === 1 ? 'person' : 'people'}
            </span>
          </div>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or select individual lists
              </span>
            </div>
          </div>

          {/* Individual Traveler Selection - always show scrollbar */}
          <div 
            className="space-y-2 max-h-[200px] overflow-y-scroll pr-2"
            style={{ 
              scrollbarWidth: 'thin',
              scrollbarGutter: 'stable'
            }}
          >
            {travelers.map((traveler) => {
              // Check if avatar is an image path (imported images become data URLs or paths with extensions)
              const isImageAvatar = traveler.avatar && (
                traveler.avatar.startsWith('/') || 
                traveler.avatar.startsWith('http') || 
                traveler.avatar.startsWith('data:') ||
                traveler.avatar.includes('.')
              );
              
              return (
                <div
                  key={traveler.id}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                    selectedTravelers.includes(traveler.id)
                      ? "border-info bg-info/10"
                      : "border-border hover:border-muted-foreground/50"
                  )}
                  onClick={() => handleTravelerToggle(traveler.id)}
                >
                  <Checkbox
                    id={`traveler-${traveler.id}`}
                    checked={selectedTravelers.includes(traveler.id)}
                    onCheckedChange={() => handleTravelerToggle(traveler.id)}
                    className="data-[state=checked]:bg-info data-[state=checked]:border-info"
                  />
                  <div className="w-8 h-8 rounded-full overflow-hidden bg-muted flex items-center justify-center text-lg shrink-0">
                    {isImageAvatar ? (
                      <img 
                        src={traveler.avatar} 
                        alt={traveler.name} 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span>{traveler.avatar || traveler.name.charAt(0)}</span>
                    )}
                  </div>
                  <Label 
                    htmlFor={`traveler-${traveler.id}`} 
                    className="cursor-pointer font-medium flex-1"
                  >
                    {traveler.name}
                  </Label>
                  {traveler.type === 'child' && (
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                      Child
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              onClick={handlePrint}
              disabled={!canPrint}
              className="bg-info hover:bg-info/90 text-info-foreground"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print {printAll ? 'All' : `${selectedTravelers.length} List${selectedTravelers.length !== 1 ? 's' : ''}`}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
