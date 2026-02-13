import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, MapPin, Calendar, Users, ArrowLeft, Pencil, Check, CalendarDays, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Logo } from "@/components/Logo";
import { useApp } from "@/context/AppContext";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { StructuredTripForm, StructuredTripData } from "./StructuredTripForm";
import { TripGenerationProgress } from "./TripGenerationProgress";
import { PackingTip } from "./PackingTip";
import { format } from "date-fns";
import { toast } from "sonner";
import { CreateTripRequest } from "@/types/trip";
export function SmartWizard() {
  const [stage, setStage] = useState<"input" | "processing">("input");
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [parsedInfo, setParsedInfo] = useState<{
    destination: string;
    duration: string;
    timeOfYear: string;
    travelers: string;
    adults: { id: string; name: string; role: string }[];
    kids: {
      name?: string;
      age: number;
    }[];
    activities: string[];
    startDate: string;
    endDate: string;
  } | null>(null);
  const { createTrip, selectTrip, auth } = useApp();
  const navigate = useNavigate();
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<'pending' | 'processing' | 'completed' | 'failed'>('pending');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Check for pending trip data after authentication
  useEffect(() => {
    const pendingTripData = sessionStorage.getItem('pending_trip_data');
    if (pendingTripData && auth.isAuthenticated && !auth.isLoading) {
      try {
        const parsedData = JSON.parse(pendingTripData);
        setParsedInfo(parsedData);
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
    setJobStatus('pending');
    setElapsedSeconds(0);
    
    // Start elapsed time counter for all users (guest and authenticated)
    timerRef.current = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);
    
    try {
      // Convert parsed info to CreateTripRequest format
      const travelers = [
        ...tripInfo.adults.map(adult => ({
          name: adult.name || adult.role,
          age: 30, // Default age for adults
          type: 'adult' as const,
        })),
        ...tripInfo.kids.map(kid => {
          // Use child name if provided, otherwise use age-based label
          let name: string;
          if (kid.name && kid.name.trim()) {
            name = kid.name;
          } else if (kid.age === 0) {
            name = 'Infant';
          } else if (kid.age === 1) {
            name = '1-yr old';
          } else {
            name = `${kid.age}-yr old`;
          }
          
          return {
            name,
            age: kid.age,
            type: kid.age < 2 ? 'infant' as const : 'child' as const,
          };
        }),
      ];
      
      const tripData: CreateTripRequest = {
        destination: tripInfo.destination,
        startDate: tripInfo.startDate,
        endDate: tripInfo.endDate,
        activities: tripInfo.activities,
        transport: [],
        travelers,
      };
      
      // Check if user is authenticated - use async job flow for authenticated users
      if (auth.isAuthenticated) {
        // Set stage to processing to show the progress spinner
        setStage("processing");
        
        // Import tripApi dynamically to avoid circular dependencies
        const { tripApi } = await import('@/lib/api');
        
        // Enqueue the trip generation job
        const { jobId } = await tripApi.enqueueTripGeneration(tripData);
        setJobStatus('processing');
        
        // Poll for job completion
        const pollInterval = 2000; // 2 seconds
        const maxAttempts = 60; // 2 minutes max
        let attempts = 0;
        
        const checkJobStatus = async (): Promise<void> => {
          attempts++;
          
          if (attempts > maxAttempts) {
            throw new Error('Trip generation timed out. Please try again.');
          }
          
          const currentJobStatus = await tripApi.getTripGenerationJobStatus(jobId);
          setJobStatus(currentJobStatus.status);
          
          if (currentJobStatus.status === 'completed') {
            if (!currentJobStatus.tripId) {
              throw new Error('Trip generation completed but no trip ID was returned.');
            }
            
            // Load the completed trip using selectTrip
            await selectTrip(currentJobStatus.tripId);
            toast.success('Trip created successfully!');
            navigate("/dashboard");
          } else if (currentJobStatus.status === 'failed') {
            throw new Error(currentJobStatus.error || 'Trip generation failed. Please try again.');
          } else {
            // Job is still pending or processing, poll again
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            await checkJobStatus();
          }
        };
        
        await checkJobStatus();
      } else {
        // Guest mode: Set stage to processing to show progress page
        setStage("processing");
        setJobStatus('processing');
        
        // Guest mode: use synchronous createTrip (which handles guest trips locally)
        await createTrip(tripData);
        
        // Mark as completed
        setJobStatus('completed');
        toast.success('Trip created successfully!');
        navigate("/");
      }
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
      // Clear the timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
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
      
      const tripInfo = {
        destination: data.destinations.join(", ") || "Tokyo, Japan",
        duration: durationText,
        timeOfYear: data.dateRange?.from ? format(data.dateRange.from, "MMMM") : "March",
        travelers: `${data.adults.length} adults${kidsText}`,
        adults: adultsData,
        kids: data.kids.length > 0 ? data.kids : [{
          name: '',
          age: 4
        }, {
          name: '',
          age: 7
        }],
        activities: data.activities,
        startDate: data.dateRange?.from ? format(data.dateRange.from, "yyyy-MM-dd") : "2025-03-28",
        endDate: data.dateRange?.to ? format(data.dateRange.to, "yyyy-MM-dd") : "2025-04-18"
      };
      
      setParsedInfo(tripInfo);
      
      // Skip confirming stage and go directly to trip creation
      await completeTripCreation(tripInfo);
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
        <Logo size="home" />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center px-6 pb-20 pt-4">
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
              <p className="text-center text-base font-medium text-muted-foreground">
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
        }} className="w-full flex justify-center">
              <TripGenerationProgress
                jobStatus={jobStatus}
                elapsedSeconds={elapsedSeconds}
                travelerCount={(parsedInfo?.adults.length || 0) + (parsedInfo?.kids.length || 0)}
                destination={parsedInfo?.destination}
                startDate={parsedInfo?.startDate}
                endDate={parsedInfo?.endDate}
                activities={parsedInfo?.activities}
              />
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

  // Helper function to get temperature description
  const getTempDescription = (temp: number): string => {
    if (temp < 40) return "very cold";
    if (temp < 55) return "cold";
    if (temp < 65) return "cool";
    if (temp < 80) return "warm";
    return "hot";
  };

  // Helper function to get weather condition description
  const getConditionDescription = (conditions: string[]): string => {
    if (conditions.includes('rainy')) return "rainy";
    if (conditions.includes('snowy')) return "snowing";
    if (conditions.includes('sunny')) return "dry";
    if (conditions.includes('cloudy')) return "cloudy";
    return "dry";
  };

  const tempDesc = getTempDescription(weather.avgTemp);
  const conditionDesc = getConditionDescription(weather.conditions);
  const lowTemp = Math.round(weather.avgTemp - 5);
  const highTemp = Math.round(weather.avgTemp + 5);
  
  const conversationalWeather = `It's going to be ${tempDesc} and ${conditionDesc}! Expect lows of ${lowTemp}°${weather.tempUnit} and highs of ${highTemp}°${weather.tempUnit}.`;

  return (
    <div className="bg-gradient-to-br from-primary/20 via-primary/10 to-accent/30 rounded-2xl p-5 border-2 border-primary/30 shadow-lg">
      <div className="flex items-start gap-3">
        <span className="text-3xl">{weatherEmoji}</span>
        <div>
          <p className="text-lg font-semibold text-primary mb-1">
            Weather Forecast
          </p>
          <p className="text-foreground mb-1">
            {conversationalWeather}
          </p>
          <p className="text-sm text-muted-foreground">
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