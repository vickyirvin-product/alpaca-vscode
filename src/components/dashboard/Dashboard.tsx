import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Menu, X, User, Map, FileText, Printer, Bookmark, Copy, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import alpacaIcon from '@/assets/alpaca-icon-only.svg';
import { TripSummaryCard } from './TripSummaryCard';
import { PersonTabBar } from './PersonTabBar';
import { PersonPackingList } from '@/components/packing/PersonPackingList';
import { KidModePackingView } from '@/components/packing/KidModePackingView';
import { ShareDialog } from '@/components/packing/ShareDialog';
import { SaveListAsTemplateDialog } from '@/components/packing/SaveListAsTemplateDialog';
import { PrintDialog } from '@/components/packing/PrintDialog';
import { AddItemDialog } from '@/components/packing/AddItemDialog';
import { useApp } from '@/context/AppContext';
import { KidModeLevel, extendedTripData } from '@/data/mockData';
import { cn } from '@/lib/utils';
const navItems = [{
  label: 'Account',
  icon: User
}, {
  label: 'Trips',
  icon: Map
}, {
  label: 'Templates',
  icon: FileText
}];
export function Dashboard() {
  const {
    trip,
    packingItems,
    travelers,
    kidMode,
    setKidMode,
    getItemsByPerson,
    getPackingProgress,
    addItem,
    setHasCompletedOnboarding,
    isLoadingTrips,
    trips
  } = useApp();
  const { toast } = useToast();
  const [shareOpen, setShareOpen] = useState(false);
  const [printDialogOpen, setPrintDialogOpen] = useState(false);
  const [saveListTemplateOpen, setSaveListTemplateOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [kidModeLevel, setKidModeLevel] = useState<KidModeLevel>('little');
  const [selectedPersonId, setSelectedPersonId] = useState(travelers[0]?.id || '');
  const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);

  // Track which travelers have had their kid mode preference set by user
  const [kidModePreferences, setKidModePreferences] = useState<Record<string, boolean>>({});

  // Handle person selection - auto-enable kid mode for children on first selection
  const handleSelectPerson = (personId: string) => {
    setSelectedPersonId(personId);
    const traveler = travelers.find(t => t.id === personId);
    if (traveler?.type === 'child') {
      // Check if user has set a preference for this child
      if (!(personId in kidModePreferences)) {
        // First time selecting this child - default to kid mode ON
        setKidMode(true);
      } else {
        // Use the user's saved preference
        setKidMode(kidModePreferences[personId]);
      }
    }
  };

  // Wrapper for setKidMode that saves user preference
  const handleSetKidMode = (enabled: boolean) => {
    setKidMode(enabled);
    const currentTraveler = travelers.find(t => t.id === selectedPersonId);
    if (currentTraveler?.type === 'child') {
      setKidModePreferences(prev => ({
        ...prev,
        [selectedPersonId]: enabled
      }));
    }
  };

  // Scroll to top when dashboard loads
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);
  // Show loading state
  if (isLoadingTrips) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading your trips...</p>
        </div>
      </div>
    );
  }

  // Show empty state if no trip is loaded
  if (!trip) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center space-y-4 max-w-md">
          <div className="w-16 h-16 mx-auto mb-4">
            <img src={alpacaIcon} alt="Alpaca" className="w-full h-full opacity-50" />
          </div>
          <h2 className="text-2xl font-bold text-secondary">No Trip Selected</h2>
          <p className="text-muted-foreground">
            {trips.length === 0
              ? "You haven't created any trips yet. Start planning your next adventure!"
              : "Select a trip from your list or create a new one."}
          </p>
          <Button
            onClick={() => setHasCompletedOnboarding(false)}
            className="mt-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New Trip
          </Button>
        </div>
      </div>
    );
  }
  const totalItems = packingItems.length;
  const packedItems = packingItems.filter(i => i.isPacked).length;
  const overallProgress = totalItems > 0 ? Math.round(packedItems / totalItems * 100) : 0;
  const selectedTraveler = travelers.find(t => t.id === selectedPersonId);
  const selectedPersonItems = selectedTraveler ? getItemsByPerson(selectedTraveler.id) : [];
  const isChildSelected = selectedTraveler?.type === 'child';
  const showKidMode = kidMode && isChildSelected;
  const handleEditTrip = () => {
    console.log('Edit trip');
  };
  const handleEditPerson = (personId: string) => {
    console.log('Edit person:', personId);
  };
  const handleManage = () => {
    console.log('Manage travelers');
  };
  const handlePrintAll = () => {
    setPrintDialogOpen(true);
  };
  const handleSaveTemplate = () => {
    setSaveListTemplateOpen(true);
  };
  const handleAddItemSubmit = (name: string, category: any, quantity: number) => {
    if (selectedTraveler) {
      addItem({
        personId: selectedTraveler.id,
        name,
        emoji: '📦',
        quantity,
        category,
        isEssential: false,
        isPacked: false,
        visibleToKid: true
      });
    }
  };
  return <div className={cn('min-h-screen transition-colors duration-300', kidMode && isChildSelected ? 'bg-gradient-to-br from-primary/10 via-kid-secondary/10 to-kid-accent/10' : 'bg-background')}>
      {/* Sticky Header with Trip Name, Trip Details, and Actions */}
      <header className="sticky top-0 z-40 bg-card/95 backdrop-blur-lg border-b border-border">
        <div className="container max-w-4xl mx-auto px-3">
          {/* Top row: Logo, Trip Name, Menu */}
          <div className="flex items-center gap-3 h-14">
            {/* Icon-only Logo - links back to home/search */}
            <button onClick={() => setHasCompletedOnboarding(false)} className="shrink-0 hover:opacity-80 transition-opacity flex items-center -mt-2.5">
              <img src={alpacaIcon} alt="Alpaca" className="h-9 w-9" />
            </button>
            
            {/* Trip Name - BIGGER */}
            <h1 className="font-bold text-secondary truncate flex-1 min-w-0 text-xl">
              {extendedTripData.title}
            </h1>

            {/* Hamburger Menu */}
            <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>

          {/* Trip Summary Card */}
          <div className="pb-2">
            <TripSummaryCard trip={trip} onEdit={handleEditTrip} />
          </div>

          {/* Action buttons row: Add Item + Print List + Save + Duplicate */}
          <div className="flex items-center gap-2 pb-3">
            {/* Add Item - inline input when open, button when closed */}
            {addItemDialogOpen ? <div className="flex-1 h-9">
                <AddItemDialog isOpen={addItemDialogOpen} onClose={() => setAddItemDialogOpen(false)} onAdd={handleAddItemSubmit} />
              </div> : <button onClick={() => setAddItemDialogOpen(true)} className="flex-1 h-9 flex items-center justify-center gap-1.5 px-3 border border-primary/30 rounded-md text-primary hover:border-primary transition-colors bg-primary/10 text-xs font-medium">
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>}

            {/* Action buttons - only show when dialog is closed */}
            {!addItemDialogOpen && <div className="flex items-center gap-1 shrink-0">
                <button onClick={handlePrintAll} className="h-9 flex items-center justify-center gap-1.5 px-3 border border-info/30 rounded-md text-info hover:border-info transition-colors bg-info/10 text-xs font-medium">
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print List</span>
                </button>
                <Button variant="ghost" size="icon" onClick={handleSaveTemplate} className="h-7 w-7" title="Save as Template">
                  <Bookmark className="w-3.5 h-3.5" />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => toast({ description: "Duplicate List feature is coming soon!" })} className="h-7 w-7" title="Duplicate List">
                  <Copy className="w-3.5 h-3.5" />
                </Button>
              </div>}
          </div>
        </div>
      </header>

      {/* Hamburger Menu Popover */}
      {mobileMenuOpen && <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-30" onClick={() => setMobileMenuOpen(false)} />
          {/* Dropdown Menu */}
          <motion.div initial={{
        opacity: 0,
        y: -8
      }} animate={{
        opacity: 1,
        y: 0
      }} exit={{
        opacity: 0,
        y: -8
      }} className="fixed right-3 top-12 z-40 bg-card border border-border rounded-lg shadow-lg py-1 min-w-[140px]">
            {navItems.map(item => <button key={item.label} className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-muted-foreground hover:text-primary hover:bg-muted/50 transition-colors" onClick={() => {
          setMobileMenuOpen(false);
        }}>
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>)}
          </motion.div>
        </>}

      {/* Main Content */}
      <main className="container max-w-4xl mx-auto px-3 py-2 space-y-3">
        {/* Person Tab Bar with integrated overall progress */}
        <PersonTabBar 
          travelers={travelers} 
          selectedPersonId={selectedPersonId} 
          onSelectPerson={handleSelectPerson} 
          onManage={handleManage} 
          getPackingProgress={getPackingProgress}
          overallProgress={overallProgress}
          packedItems={packedItems}
          totalItems={totalItems}
        />

        {/* Packing List Content */}
        {selectedTraveler && (showKidMode ? <KidModePackingView items={selectedPersonItems} personName={selectedTraveler.name} personId={selectedTraveler.id} kidModeLevel={kidModeLevel} setKidModeLevel={setKidModeLevel} kidMode={kidMode} setKidMode={handleSetKidMode} /> : <motion.div key={selectedPersonId} initial={{
        opacity: 0,
        y: 10
      }} animate={{
        opacity: 1,
        y: 0
      }}>
              <PersonPackingList personId={selectedTraveler.id} personName={selectedTraveler.name} avatar={selectedTraveler.avatar || '👤'} items={selectedPersonItems} isKidMode={false} isChild={selectedTraveler.type === 'child'} kidMode={kidMode} setKidMode={handleSetKidMode} kidModeLevel={kidModeLevel} setKidModeLevel={setKidModeLevel} />
            </motion.div>)}
      </main>

      {/* Share Dialog */}
      <ShareDialog open={shareOpen} onOpenChange={setShareOpen} itemCount={5} />

      {/* Print Dialog */}
      <PrintDialog open={printDialogOpen} onOpenChange={setPrintDialogOpen} travelers={travelers} />

      {/* Save List as Template Dialog */}
      <SaveListAsTemplateDialog open={saveListTemplateOpen} onOpenChange={setSaveListTemplateOpen} tripName={extendedTripData.title} itemCount={totalItems} />

    </div>;
}