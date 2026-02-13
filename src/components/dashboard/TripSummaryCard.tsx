import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, 
  Calendar, 
  Cloud, 
  Thermometer,
  Pencil,
  X,
  Plus,
  MoreHorizontal,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { TripInfo } from '@/types/packing';

interface TripSummaryCardProps {
  trip: TripInfo;
  onEdit?: () => void;
}

export function TripSummaryCard({ trip, onEdit }: TripSummaryCardProps) {
  // Use activities from trip prop, fallback to empty array
  const tripActivities = trip.activities || [];
  const [activities, setActivities] = useState<string[]>(tripActivities);
  const [visibleCount, setVisibleCount] = useState(activities.length);
  const [showAllPopover, setShowAllPopover] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Generate conversational weather summary
  const getConversationalWeather = () => {
    if (!trip.weather) return null;
    
    const tempDesc = getTempDescription(trip.weather.avgTemp);
    const conditionDesc = getConditionDescription(trip.weather.conditions);
    
    // For now, we'll use avgTemp as both high and low (can be enhanced with actual data)
    const lowTemp = Math.round(trip.weather.avgTemp - 5);
    const highTemp = Math.round(trip.weather.avgTemp + 5);
    
    return `It's going to be ${tempDesc} and ${conditionDesc}! Expect lows of ${lowTemp}°${trip.weather.tempUnit} and highs of ${highTemp}°${trip.weather.tempUnit}.`;
  };

  // Calculate how many tags fit in the available space
  useEffect(() => {
    const calculateVisibleTags = () => {
      if (!containerRef.current) return;
      const containerWidth = containerRef.current.offsetWidth;
      const availableWidth = containerWidth - 100;
      const avgTagWidth = 80;
      const maxVisible = Math.max(1, Math.floor(availableWidth / avgTagWidth));
      setVisibleCount(Math.min(maxVisible, activities.length));
    };

    calculateVisibleTags();
    window.addEventListener('resize', calculateVisibleTags);
    return () => window.removeEventListener('resize', calculateVisibleTags);
  }, [activities.length]);

  const handleRemoveActivity = (activity: string) => {
    setActivities(prev => prev.filter(a => a !== activity));
  };

  const handleAddActivity = () => {
    const newActivity = prompt('Enter new activity:');
    if (newActivity && !activities.includes(newActivity)) {
      setActivities(prev => [...prev, newActivity]);
    }
  };


  // Parse date to get month
  const startDate = new Date(trip.startDate);
  const monthName = startDate.toLocaleString('default', { month: 'long' });

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Trip Details Card - Contained with distinct background */}
      <div className="bg-secondary/5 border border-secondary/10 rounded-xl overflow-hidden">
        {/* Card Header - entire row is clickable */}
        <div 
          onClick={() => setIsDetailsOpen(!isDetailsOpen)}
          className="flex items-center justify-between px-4 py-2.5 cursor-pointer hover:bg-secondary/10 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Trip Details & Weather
            </span>
            {isDetailsOpen ? (
              <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => { e.stopPropagation(); onEdit?.(); }}
            className="h-4 w-4 p-0 text-muted-foreground hover:text-primary"
          >
            <Pencil className="w-2 h-2" />
          </Button>
        </div>

        {/* Collapsible Content */}
        <AnimatePresence>
          {isDetailsOpen && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-3">
                {/* Locations with individual pins */}
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <MapPin className="w-3.5 h-3.5 text-primary" />
                    {trip.destination}
                  </span>
                </div>

                {/* Date & Weather Row */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-primary" />
                    {trip.duration} days in {monthName}
                  </span>
                  {trip.weather && (
                    <span className="flex items-center gap-1.5">
                      <Thermometer className="w-3.5 h-3.5 text-primary" />
                      {trip.weather.avgTemp}°{trip.weather.tempUnit}
                    </span>
                  )}
                </div>

                {/* Activity Tags */}
                <div ref={containerRef} className="flex flex-wrap items-center gap-1.5">
                  {activities.slice(0, visibleCount).map((activity) => (
                    <Badge 
                      key={activity} 
                      variant="outline" 
                      className="text-xs px-2.5 py-0.5 bg-muted/80 border-muted-foreground/20 text-muted-foreground group hover:border-destructive/50 shrink-0"
                    >
                      {activity}
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRemoveActivity(activity); }}
                        className="ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity hover:text-destructive"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                  
                  {/* See All popover when tags overflow */}
                  {activities.length > visibleCount && (
                    <Popover open={showAllPopover} onOpenChange={setShowAllPopover}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-xs text-muted-foreground hover:text-primary"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreHorizontal className="w-3.5 h-3.5" />
                          <span className="ml-0.5">+{activities.length - visibleCount}</span>
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-2" align="start">
                        <div className="flex flex-wrap gap-1.5 max-w-xs">
                          {activities.map((activity) => (
                            <Badge 
                              key={activity} 
                              variant="outline" 
                              className="text-xs px-2.5 py-0.5 bg-muted/80 border-muted-foreground/20 text-muted-foreground group hover:border-destructive/50"
                            >
                              {activity}
                              <button
                                onClick={() => handleRemoveActivity(activity)}
                                className="ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity hover:text-destructive"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </Badge>
                          ))}
                        </div>
                      </PopoverContent>
                    </Popover>
                  )}

                  {/* Add button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => { e.stopPropagation(); handleAddActivity(); }}
                    className="h-6 w-6 text-muted-foreground hover:text-primary"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </Button>
                </div>

                {/* Weather Insight Card - Conversational format */}
                {trip.weather && (
                  <div className="bg-primary/10 border border-primary/30 rounded-xl px-3 py-2.5">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-sm">
                        {trip.weather.conditions.includes('sunny') ? '☀️' :
                         trip.weather.conditions.includes('rainy') ? '🌧️' :
                         trip.weather.conditions.includes('snowy') ? '❄️' :
                         trip.weather.conditions.includes('cloudy') ? '☁️' : '🌤️'}
                      </span>
                      <span className="text-xs font-semibold text-primary">
                        Weather Forecast
                      </span>
                    </div>
                    <p className="text-xs text-foreground leading-relaxed mb-1">
                      {getConversationalWeather()}
                    </p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {trip.weather.recommendation}
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
