import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, MapPin, Calendar, Users, ArrowLeft, Pencil, Check, CalendarDays, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Logo } from "@/components/Logo";
import { useApp } from "@/context/AppContext";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { StructuredTripForm, StructuredTripData } from "./StructuredTripForm";
import { format } from "date-fns";
import { toast } from "sonner";
import { CreateTripRequest } from "@/types/trip";
export function SmartWizard() {
  const [stage, setStage] = useState<"input" | "processing" | "confirming">("input");
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [parsedInfo, setParsedInfo] = useState<{
    destination: string;
    duration: string;
    timeOfYear: string;
    travelers: string;
    adults: { id: string; name: string; role: string }[];
    kids: {
      age: number;
    }[];
    activities: string[];
    startDate: string;
    endDate: string;
  } | null>(null);
  const { createTrip, auth } = useApp();
  const navigate = useNavigate();
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for pending trip data after authentication
  useEffect(() => {
    const pendingTripData = sessionStorage.getItem('pending_trip_data');
    if (pendingTripData && auth.isAuthenticated && !auth.isLoading) {
      try {
        const parsedData = JSON.parse(pendingTripData);
        setParsedInfo(parsedData);
        setStage("confirming");
        sessionStorage.removeItem('pending_trip_data');
        // Automatically trigger trip creation
        setTimeout(() => {
          completeTripCreation(parsedData);
        }, 100);
      } catch (err) {
        console.error('Failed to parse pending trip data:', err);
        sessionStorage.removeItem('pending_trip_data');
      }
    }
  }, [auth.isAuthenticated, auth.isLoading]);

  const completeTripCreation = async (tripInfo: typeof parsedInfo) => {
    if (!tripInfo) return;
    
    setIsCreating(true);
    setError(null);
    
    try {
      // Convert parsed info to CreateTripRequest format
      const travelers = [
        ...tripInfo.adults.map(adult => ({
          name: adult.name || adult.role,
          age: 30, // Default age for adults
          type: 'adult' as const,
        })),
        ...tripInfo.kids.map(kid => ({
          name: `Child (${kid.age})`,
          age: kid.age,
          type: kid.age < 2 ? 'infant' as const : 'child' as const,
        })),
      ];
      
      const tripData: CreateTripRequest = {
        destination: tripInfo.destination,
        startDate: tripInfo.startDate,
        endDate: tripInfo.endDate,
        activities: tripInfo.activities,
        transport: [],
        travelers,
      };
      
      await createTrip(tripData);
      toast.success('Trip created successfully!');
      
      // Navigate to appropriate route based on auth status
      // Guest users go to "/" (public), authenticated users go to "/dashboard" (protected)
      navigate(auth.isAuthenticated ? "/dashboard" : "/");
    } catch (err) {
      console.error('Failed to create trip:', err);
      
      // Provide user-friendly error messages based on error type
      let errorMessage = 'Unable to create trip. Please try again.';
      
      if (err instanceof Error) {
        // Check for specific error patterns
        if (err.message.includes('quota') || err.message.includes('rate limit')) {
          errorMessage = 'Service temporarily unavailable. Please try again in a few moments.';
        } else if (err.message.includes('validation')) {
          errorMessage = 'Invalid trip information. Please check your details and try again.';
        } else if (err.message.includes('network') || err.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else if (err.message.includes('weather')) {
          errorMessage = 'Unable to fetch weather data. Please try again.';
        } else if (err.message.includes('packing list')) {
          errorMessage = 'Failed to generate packing list. Please try again.';
        } else if (err.message) {
          // Use the actual error message if it's user-friendly
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      toast.error(errorMessage, {
        duration: 5000,
        description: 'If the problem persists, please contact support.'
      });
    } finally {
      setIsCreating(false);
    }
  };
  
  const handleConfirm = async () => {
    if (!parsedInfo) return;
    
    // Allow trip creation regardless of auth status
    // The createTrip function in AppContext will handle guest vs authenticated mode
    await completeTripCreation(parsedInfo);
  };
  const handleRestart = () => {
    setStage("input");
    setParsedInfo(null);
    setEditingField(null);
    setEditValues({});
  };
  const handleEditField = (field: string, value: string) => {
    setEditingField(field);
    setEditValues({
      ...editValues,
      [field]: value
    });
  };
  const handleSaveField = (field: string) => {
    if (parsedInfo && editValues[field] !== undefined) {
      const newParsedInfo = {
        ...parsedInfo
      };
      if (field === 'destination') newParsedInfo.destination = editValues[field];
      if (field === 'duration') newParsedInfo.duration = editValues[field];
      if (field === 'timeOfYear') newParsedInfo.timeOfYear = editValues[field];
      if (field === 'startDate') newParsedInfo.startDate = editValues[field];
      if (field === 'endDate') newParsedInfo.endDate = editValues[field];
      setParsedInfo(newParsedInfo);
    }
    setEditingField(null);
  };
  const handleStructuredSubmit = async (data: StructuredTripData) => {
    setStage("processing");
    setError(null);
    
    try {
      const durationDays = data.dateRange?.from && data.dateRange?.to
        ? Math.ceil((data.dateRange.to.getTime() - data.dateRange.from.getTime()) / (1000 * 60 * 60 * 24))
        : 14;
      const weeks = Math.round(durationDays / 7);
      const durationText = weeks >= 1 ? `${weeks} week${weeks > 1 ? 's' : ''}` : `${durationDays} days`;
      const kidsText = data.kids.length > 0 ? `, ${data.kids.length} kids (ages ${data.kids.map(k => k.age).join(' and ')})` : '';
      
      // Use provided adults data or create default
      const adultsData = data.adults.length > 0 ? data.adults : [
        { id: '1', name: '', role: 'Mom' },
        { id: '2', name: '', role: 'Dad' }
      ];
      
      setParsedInfo({
        destination: data.destinations.join(", ") || "Tokyo, Japan",
        duration: durationText,
        timeOfYear: data.dateRange?.from ? format(data.dateRange.from, "MMMM") : "March",
        travelers: `${data.adults.length} adults${kidsText}`,
        adults: adultsData,
        kids: data.kids.length > 0 ? data.kids : [{
          age: 4
        }, {
          age: 7
        }],
        activities: data.activities,
        startDate: data.dateRange?.from ? format(data.dateRange.from, "yyyy-MM-dd") : "2025-03-28",
        endDate: data.dateRange?.to ? format(data.dateRange.to, "yyyy-MM-dd") : "2025-04-18"
      });
      
      setStage("confirming");
    } catch (err) {
      console.error('Failed to process trip data:', err);
      setError(err instanceof Error ? err.message : 'Failed to process trip data');
      toast.error('Failed to process trip data');
      setStage("input");
    }
  };
  return <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="p-3">
        <Logo size="md" />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
        <AnimatePresence mode="wait">
          {stage === "input" && <motion.div key="input" initial={{
          opacity: 0,
          y: 20
        }} animate={{
          opacity: 1,
          y: 0
        }} exit={{
          opacity: 0,
          y: -20
        }} className="w-full max-w-2xl space-y-2">
              {/* Tagline */}
              <p className="text-center -mt-6 text-base font-medium text-muted-foreground">
                Family packing, simplified
              </p>

              {/* Hero Text */}
              <div className="text-center">
                <h1 className="text-4xl md:text-5xl font-bold text-secondary">
                  What trip are you packing for?
                </h1>
              </div>

              {/* Form Content */}
              <div className="min-h-[400px]">
                <StructuredTripForm onSubmit={handleStructuredSubmit} />
              </div>
            </motion.div>}

          {stage === "processing" && <motion.div key="processing" initial={{
          opacity: 0,
          scale: 0.9
        }} animate={{
          opacity: 1,
          scale: 1
        }} exit={{
          opacity: 0,
          scale: 0.9
        }} className="text-center space-y-6">
              <div className="relative">
                <motion.div animate={{
              rotate: 360
            }} transition={{
              duration: 2,
              repeat: Infinity,
              ease: "linear"
            }} className="w-24 h-24 mx-auto">
                  <Sparkles className="w-24 h-24 text-primary" />
                </motion.div>
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold text-secondary">Creating your packing list...</h2>
                <p className="text-muted-foreground">
                  Checking weather, calculating quantities, adding age-appropriate items
                </p>
              </div>
            </motion.div>}

          {stage === "confirming" && parsedInfo && <motion.div key="confirming" initial={{
          opacity: 0,
          y: 20
        }} animate={{
          opacity: 1,
          y: 0
        }} exit={{
          opacity: 0,
          y: -20
        }} className="w-full max-w-2xl space-y-6">
              {/* Weather Speech Bubble - Fetch and display weather immediately */}
              <WeatherPreview
                destination={parsedInfo.destination}
                startDate={parsedInfo.startDate}
                endDate={parsedInfo.endDate}
              />

              {/* Duplicate Action Buttons */}
              <div className="space-y-3">
                {error && (
                  <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
                    {error}
                  </div>
                )}
                <Button
                  onClick={handleConfirm}
                  size="lg"
                  className="w-full rounded-xl h-14 text-lg font-semibold"
                  disabled={isCreating}
                >
                  {isCreating ? 'Creating Trip...' : 'View My Packing List'}
                </Button>
                <Button
                  variant="ghost"
                  onClick={handleRestart}
                  className="w-full text-muted-foreground hover:text-foreground"
                  disabled={isCreating}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Start Over
                </Button>
              </div>

              {/* Confirmation Card */}
              <div className="bg-card rounded-3xl p-8 card-shadow-lg border border-border">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-secondary">Trip Summary</h2>
                    <p className="text-muted-foreground mt-1">Click any field to edit it</p>
                  </div>
                </div>

                <div className="space-y-3 mb-6">
                  {/* Destination */}
                  <EditableField icon={<MapPin className="w-5 h-5 text-primary" />} label="Destination" value={parsedInfo.destination} isEditing={editingField === 'destination'} editValue={editValues['destination'] || parsedInfo.destination} onEdit={() => handleEditField('destination', parsedInfo.destination)} onSave={() => handleSaveField('destination')} onChange={v => setEditValues({
                ...editValues,
                destination: v
              })} />

                  {/* Dates */}
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-xl group">
                    <CalendarDays className="w-5 h-5 text-primary" />
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground">Dates</p>
                      {editingField === 'dates' ? <div className="flex gap-2 items-center mt-1">
                          <Input value={editValues['startDate'] || parsedInfo.startDate} onChange={e => setEditValues({
                      ...editValues,
                      startDate: e.target.value
                    })} className="h-8 text-sm" placeholder="Start date" />
                          <span className="text-muted-foreground">to</span>
                          <Input value={editValues['endDate'] || parsedInfo.endDate} onChange={e => setEditValues({
                      ...editValues,
                      endDate: e.target.value
                    })} className="h-8 text-sm" placeholder="End date" />
                          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => {
                      if (parsedInfo) {
                        setParsedInfo({
                          ...parsedInfo,
                          startDate: editValues['startDate'] || parsedInfo.startDate,
                          endDate: editValues['endDate'] || parsedInfo.endDate
                        });
                      }
                      setEditingField(null);
                    }}>
                            <Check className="h-4 w-4" />
                          </Button>
                        </div> : <div className="flex items-center gap-2">
                          <p className="font-medium text-secondary">{parsedInfo.startDate} → {parsedInfo.endDate}</p>
                          <Button size="icon" variant="ghost" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => {
                      setEditingField('dates');
                      setEditValues({
                        ...editValues,
                        startDate: parsedInfo.startDate,
                        endDate: parsedInfo.endDate
                      });
                    }}>
                            <Pencil className="h-3 w-3" />
                          </Button>
                        </div>}
                    </div>
                  </div>

                  {/* Duration */}
                  <EditableField icon={<Calendar className="w-5 h-5 text-primary" />} label="Duration" value={parsedInfo.duration} isEditing={editingField === 'duration'} editValue={editValues['duration'] || parsedInfo.duration} onEdit={() => handleEditField('duration', parsedInfo.duration)} onSave={() => handleSaveField('duration')} onChange={v => setEditValues({
                ...editValues,
                duration: v
              })} />

                  {/* Time of Year */}
                  <EditableField icon={<CalendarDays className="w-5 h-5 text-primary" />} label="Time of Year" value={parsedInfo.timeOfYear} isEditing={editingField === 'timeOfYear'} editValue={editValues['timeOfYear'] || parsedInfo.timeOfYear} onEdit={() => handleEditField('timeOfYear', parsedInfo.timeOfYear)} onSave={() => handleSaveField('timeOfYear')} onChange={v => setEditValues({
                ...editValues,
                timeOfYear: v
              })} />

                  {/* Travelers - Adults */}
                  <div className="flex items-start gap-3 p-4 bg-muted rounded-xl">
                    <Users className="w-5 h-5 text-primary mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground mb-2">Adults</p>
                      <div className="space-y-2">
                        {parsedInfo.adults.map((adult, idx) => {
                          // Count how many adults have the same role up to this point
                          const sameRoleAdults = parsedInfo.adults.filter((a, i) => a.role === adult.role && i <= idx);
                          const roleCount = sameRoleAdults.length;
                          const displayName = adult.name || `${adult.role}${parsedInfo.adults.filter(a => a.role === adult.role).length > 1 ? ` ${roleCount}` : ''}`;
                          
                          return (
                            <div key={adult.id} className="flex items-center gap-2">
                              <Badge variant="secondary" className="px-3 py-1.5 text-sm">
                                {displayName}
                              </Badge>
                              <span className="text-xs text-muted-foreground">({adult.role})</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Kids */}
                  {parsedInfo.kids.length > 0 && <div className="flex items-start gap-3 p-4 bg-muted rounded-xl">
                      <Users className="w-5 h-5 text-primary mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-muted-foreground mb-2">Kids</p>
                        <div className="flex flex-wrap gap-2">
                          {parsedInfo.kids.map((kid, idx) => <Badge key={idx} variant="secondary" className="px-3 py-1.5 text-sm">
                              👶 Age {kid.age}
                            </Badge>)}
                        </div>
                      </div>
                    </div>}

                  {/* Activities */}
                  {parsedInfo.activities.length > 0 && <div className="flex items-start gap-3 p-4 bg-muted rounded-xl">
                      <Activity className="w-5 h-5 text-primary mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-muted-foreground mb-2">Activities</p>
                        <div className="flex flex-wrap gap-2">
                          {parsedInfo.activities.map(activity => <Badge key={activity} className="px-3 py-1.5">
                              {activity}
                            </Badge>)}
                        </div>
                      </div>
                    </div>}
                </div>

                <div className="space-y-3">
                  {error && (
                    <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
                      {error}
                    </div>
                  )}
                  <Button
                    onClick={handleConfirm}
                    size="lg"
                    className="w-full rounded-xl h-14 text-lg font-semibold"
                    disabled={isCreating}
                  >
                    {isCreating ? 'Creating Trip...' : 'View My Packing List'}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={handleRestart}
                    className="w-full text-muted-foreground hover:text-foreground"
                    disabled={isCreating}
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Start Over
                  </Button>
                </div>
              </div>
            </motion.div>}
        </AnimatePresence>
      </main>
    </div>;
}

// Weather Preview Component
function WeatherPreview({ destination, startDate, endDate }: { destination: string; startDate: string; endDate: string }) {
  const [weather, setWeather] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setLoading(true);
        setError(false);
        
        const { weatherApi } = await import('@/lib/api');
        const weatherData = await weatherApi.getForecast(destination, startDate, endDate);
        setWeather(weatherData);
      } catch (err) {
        console.error('Failed to fetch weather preview:', err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();
  }, [destination, startDate, endDate]);

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-primary/20 via-primary/10 to-accent/30 rounded-2xl p-5 border-2 border-primary/30 shadow-lg">
        <div className="flex items-start gap-3">
          <span className="text-3xl">🌤️</span>
          <div>
            <p className="text-lg font-semibold text-primary mb-1">Weather Information</p>
            <p className="text-muted-foreground">
              Fetching weather forecast...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !weather) {
    return (
      <div className="bg-gradient-to-br from-primary/20 via-primary/10 to-accent/30 rounded-2xl p-5 border-2 border-primary/30 shadow-lg">
        <div className="flex items-start gap-3">
          <span className="text-3xl">🌤️</span>
          <div>
            <p className="text-lg font-semibold text-primary mb-1">Weather Information</p>
            <p className="text-muted-foreground">
              Unable to fetch weather data. We'll try again when you create your trip.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const weatherEmoji = weather.conditions.includes('sunny') ? '☀️' :
                      weather.conditions.includes('rainy') ? '🌧️' :
                      weather.conditions.includes('snowy') ? '❄️' :
                      weather.conditions.includes('cloudy') ? '☁️' : '🌤️';

  return (
    <div className="bg-gradient-to-br from-primary/20 via-primary/10 to-accent/30 rounded-2xl p-5 border-2 border-primary/30 shadow-lg">
      <div className="flex items-start gap-3">
        <span className="text-3xl">{weatherEmoji}</span>
        <div>
          <p className="text-lg font-semibold text-primary mb-1">
            {weather.avgTemp}°{weather.tempUnit} - {weather.conditions.join(', ')}
          </p>
          <p className="text-muted-foreground">
            {weather.recommendation}
          </p>
        </div>
      </div>
    </div>
  );
}

// Editable field component
function EditableField({
  icon,
  label,
  value,
  isEditing,
  editValue,
  onEdit,
  onSave,
  onChange
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  isEditing: boolean;
  editValue: string;
  onEdit: () => void;
  onSave: () => void;
  onChange: (value: string) => void;
}) {
  return <div className="flex items-center gap-3 p-4 bg-muted rounded-xl group">
      {icon}
      <div className="flex-1">
        <p className="text-sm text-muted-foreground">{label}</p>
        {isEditing ? <div className="flex gap-2 items-center mt-1">
            <Input value={editValue} onChange={e => onChange(e.target.value)} className="h-8 text-sm" autoFocus />
            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={onSave}>
              <Check className="h-4 w-4" />
            </Button>
          </div> : <div className="flex items-center gap-2">
            <p className="font-medium text-secondary">{value}</p>
            <Button size="icon" variant="ghost" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity" onClick={onEdit}>
              <Pencil className="h-3 w-3" />
            </Button>
          </div>}
      </div>
    </div>;
}