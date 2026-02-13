import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Calendar, Users, Plus, Minus, X, Search, Plane, Car, Ship } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format, differenceInDays } from "date-fns";
import { cn } from "@/lib/utils";
import { DateRange } from "react-day-picker";
import { LocationAutocomplete } from "@/components/ui/location-autocomplete";

const activityTags = ["Walking/Hiking", "Sightseeing", "Staying with family", "Skiing/Snowboarding", "Camping", "Beach", "Pool", "Theme Park", "Nice Restaurants/Event"];
const transportOptions = [
  { id: "flying", label: "Flying", icon: Plane },
  { id: "driving", label: "Driving", icon: Car },
  { id: "cruise", label: "Cruise", icon: Ship },
];

export interface StructuredTripData {
  destinations: string[];
  dateRange: DateRange | undefined;
  adults: { id: string; name: string; role: string }[];
  kids: { name: string; age: number }[];
  activities: string[];
  transport: string[];
}

interface StructuredTripFormProps {
  initialData?: Partial<StructuredTripData>;
  onSubmit: (data: StructuredTripData) => void;
}

export function StructuredTripForm({ initialData, onSubmit }: StructuredTripFormProps) {
  const [expandedSection, setExpandedSection] = useState<"where" | "when" | "who" | "activities" | null>("where");
  const [destinations, setDestinations] = useState<string[]>(initialData?.destinations || []);
  const [dateRange, setDateRange] = useState<DateRange | undefined>(initialData?.dateRange);
  const [adultsData, setAdultsData] = useState<{ id: string; name: string; role: string }[]>(initialData?.adults || []);
  const [kids, setKids] = useState<{ name: string; age: number }[]>(initialData?.kids || []);
  const [selectedActivities, setSelectedActivities] = useState<string[]>(initialData?.activities || []);
  const [selectedTransport, setSelectedTransport] = useState<string[]>(initialData?.transport || []);
  const [customActivityInput, setCustomActivityInput] = useState("");
  const [customActivities, setCustomActivities] = useState<string[]>([]);
  const [customTransportInput, setCustomTransportInput] = useState("");
  const [customTransport, setCustomTransport] = useState<string[]>([]);
  const [showKidNameInputs, setShowKidNameInputs] = useState<boolean[]>([]);
  const [kidAgeErrors, setKidAgeErrors] = useState<boolean[]>([]);

  // Sync with initialData when it changes
  useEffect(() => {
    if (initialData?.destinations && initialData.destinations.length > 0 && destinations.length === 0) {
      setDestinations(initialData.destinations);
    }
    if (initialData?.dateRange && !dateRange) {
      setDateRange(initialData.dateRange);
    }
    if (initialData?.adults && initialData.adults.length > 0 && adultsData.length === 0) {
      setAdultsData(initialData.adults);
    }
    if (initialData?.kids && initialData.kids.length > 0 && kids.length === 0) {
      setKids(initialData.kids);
    }
    if (initialData?.activities && initialData.activities.length > 0) {
      setSelectedActivities(initialData.activities);
    }
    if (initialData?.transport && initialData.transport.length > 0) {
      setSelectedTransport(initialData.transport);
    }
  }, [initialData]);

  const addDestination = (dest: string, placeId?: string) => {
    if (dest.trim() && !destinations.includes(dest)) {
      setDestinations([...destinations, dest]);
    }
  };

  const removeDestination = (dest: string) => {
    setDestinations(destinations.filter(d => d !== dest));
  };

  const addKid = () => {
    setKids([...kids, { name: '', age: -1 }]); // -1 indicates "select age" placeholder
    setShowKidNameInputs([...showKidNameInputs, false]);
    setKidAgeErrors([...kidAgeErrors, false]);
  };

  const removeKid = () => {
    if (kids.length > 0) {
      setKids(kids.slice(0, -1));
      setShowKidNameInputs(showKidNameInputs.slice(0, -1));
      setKidAgeErrors(kidAgeErrors.slice(0, -1));
    }
  };

  const updateKidName = (index: number, name: string) => {
    const newKids = [...kids];
    newKids[index] = { ...newKids[index], name };
    setKids(newKids);
  };

  const updateKidAge = (index: number, age: number) => {
    const newKids = [...kids];
    newKids[index] = { ...newKids[index], age };
    setKids(newKids);
    
    // Clear error when age is selected
    if (age >= 0) {
      const newErrors = [...kidAgeErrors];
      newErrors[index] = false;
      setKidAgeErrors(newErrors);
    }
  };

  const toggleActivity = (activity: string) => {
    setSelectedActivities(prev =>
      prev.includes(activity)
        ? prev.filter(a => a !== activity)
        : [...prev, activity]
    );
  };

  const toggleTransport = (transport: string) => {
    setSelectedTransport(prev =>
      prev.includes(transport)
        ? prev.filter(t => t !== transport)
        : [...prev, transport]
    );
  };

  const addCustomActivity = (activity: string) => {
    if (!customActivities.includes(activity) && !activityTags.includes(activity)) {
      setCustomActivities([...customActivities, activity]);
    }
    setCustomActivityInput("");
  };

  const removeCustomActivity = (activity: string) => {
    setCustomActivities(customActivities.filter(a => a !== activity));
  };

  const addCustomTransport = (transport: string) => {
    if (!customTransport.includes(transport) && !transportOptions.some(o => o.label === transport)) {
      setCustomTransport([...customTransport, transport]);
    }
    setCustomTransportInput("");
  };

  const removeCustomTransport = (transport: string) => {
    setCustomTransport(customTransport.filter(t => t !== transport));
  };

  const addAdult = () => {
    const newId = Date.now().toString();
    const existingRoles = adultsData.map(a => a.role);
    
    // Smart default for role
    let defaultRole = "Mom";
    if (adultsData.length === 1) {
      // Second adult defaults opposite of first
      if (existingRoles[0] === "Mom") defaultRole = "Dad";
      else if (existingRoles[0] === "Dad") defaultRole = "Mom";
    }
    
    setAdultsData([...adultsData, { id: newId, name: '', role: defaultRole }]);
  };

  const removeAdult = () => {
    if (adultsData.length > 0) {
      setAdultsData(adultsData.slice(0, -1));
    }
  };

  const updateAdultName = (id: string, name: string) => {
    setAdultsData(adultsData.map(adult =>
      adult.id === id ? { ...adult, name } : adult
    ));
  };

  const updateAdultRole = (id: string, role: string) => {
    setAdultsData(adultsData.map(adult =>
      adult.id === id ? { ...adult, role } : adult
    ));
  };

  const handleSubmit = () => {
    onSubmit({
      destinations,
      dateRange,
      adults: adultsData,
      kids,
      activities: [...selectedActivities, ...customActivities],
      transport: [...selectedTransport, ...customTransport],
    });
  };

  const validateKidAges = () => {
    const errors = kids.map(kid => kid.age < 0);
    setKidAgeErrors(errors);
    return !errors.some(e => e);
  };

  const canSubmit = destinations.length > 0 &&
    dateRange?.from &&
    (adultsData.length > 0 || kids.length > 0) &&
    (selectedActivities.length > 0 || customActivities.length > 0) &&
    kids.every(kid => kid.age >= 0);

  const getDurationText = () => {
    if (!dateRange?.from || !dateRange?.to) return "";
    const days = differenceInDays(dateRange.to, dateRange.from);
    return `${days} ${days === 1 ? 'day' : 'days'}`;
  };

  return (
    <div className="w-full max-w-2xl space-y-4">
      {/* Where Section */}
      <motion.div
        className={cn(
          "bg-card rounded-2xl border border-border transition-shadow",
          expandedSection === "where" ? "card-shadow-lg overflow-visible" : "card-shadow overflow-hidden"
        )}
      >
        <button
          onClick={() => setExpandedSection(expandedSection === "where" ? null : "where")}
          className="w-full p-4 text-left flex items-center justify-between"
        >
          <span className="text-muted-foreground">Where</span>
          {expandedSection !== "where" && destinations.length > 0 && (
            <span className="text-sm font-medium text-foreground">
              {destinations[0]}
              {destinations.length > 1 && ` +${destinations.length - 1}`}
            </span>
          )}
        </button>
        
        <AnimatePresence>
          {expandedSection === "where" && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-visible"
            >
              <div className="px-4 pb-4 space-y-4">
                {/* Selected destinations */}
                {destinations.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {destinations.map(dest => (
                      <Badge key={dest} variant="default" className="pl-3 pr-1 py-1 flex items-center gap-1">
                        {dest}
                        <button
                          onClick={() => removeDestination(dest)}
                          className="ml-1 hover:bg-primary-foreground/20 rounded-full p-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Location autocomplete */}
                <LocationAutocomplete
                  value=""
                  onChange={addDestination}
                  placeholder="Search destinations"
                  autoFocus={expandedSection === "where"}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* When Section */}
      <motion.div
        className={cn(
          "bg-card rounded-2xl border border-border overflow-hidden transition-shadow",
          expandedSection === "when" ? "card-shadow-lg" : "card-shadow"
        )}
      >
        <button
          onClick={() => setExpandedSection(expandedSection === "when" ? null : "when")}
          className="w-full p-4 text-left flex items-center justify-between"
        >
          <span className="text-muted-foreground">When</span>
          {expandedSection !== "when" && dateRange?.from && (
            <span className="text-sm font-medium text-foreground">
              {format(dateRange.from, "MMM d")}
              {dateRange.to && ` - ${format(dateRange.to, "d")}`}
            </span>
          )}
        </button>
        
        <AnimatePresence>
          {expandedSection === "when" && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-4">
                <div className="flex justify-center">
                  <CalendarComponent
                    mode="range"
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={1}
                    className="rounded-xl border pointer-events-auto"
                  />
                </div>
                
                {getDurationText() && (
                  <p className="text-center text-sm text-muted-foreground">
                    Trip duration: <span className="font-medium text-secondary">{getDurationText()}</span>
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Who Section */}
      <motion.div
        className={cn(
          "bg-card rounded-2xl border border-border overflow-hidden transition-shadow",
          expandedSection === "who" ? "card-shadow-lg" : "card-shadow"
        )}
      >
        <button
          onClick={() => setExpandedSection(expandedSection === "who" ? null : "who")}
          className="w-full p-4 text-left flex items-center justify-between"
        >
          <span className="text-muted-foreground">Who</span>
          {expandedSection !== "who" && (adultsData.length > 0 || kids.length > 0) && (
            <span className="text-sm font-medium text-foreground">
              {adultsData.length + kids.length} {adultsData.length + kids.length === 1 ? "guest" : "guests"}
            </span>
          )}
        </button>
        
        <AnimatePresence>
          {expandedSection === "who" && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-4">
                {/* Adults */}
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-secondary">Adults</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="icon"
                      className="rounded-full h-8 w-8"
                      onClick={removeAdult}
                      disabled={adultsData.length === 0}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-8 text-center font-medium">{adultsData.length}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="rounded-full h-8 w-8"
                      onClick={addAdult}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Adults roles only */}
                {adultsData.length > 0 && (
                  <div className="flex flex-wrap gap-3">
                    {adultsData.map((adult, index) => (
                      <select
                        key={adult.id}
                        value={adult.role}
                        onChange={(e) => updateAdultRole(adult.id, e.target.value)}
                        className="rounded-xl border border-border bg-background px-4 py-2 text-base h-10 min-w-[120px]"
                      >
                        <option value="Mom">Mom</option>
                        <option value="Dad">Dad</option>
                        <option value="Grandma">Grandma</option>
                        <option value="Grandpa">Grandpa</option>
                        <option value="Other">Other</option>
                      </select>
                    ))}
                  </div>
                )}

                {/* Separator between Adults and Kids */}
                <div className="border-t border-border my-2"></div>

                {/* Kids */}
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-secondary">Kids</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="icon"
                      className="rounded-full h-8 w-8"
                      onClick={removeKid}
                      disabled={kids.length === 0}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-8 text-center font-medium">{kids.length}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="rounded-full h-8 w-8"
                      onClick={addKid}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Kids ages */}
                {kids.length > 0 && (
                  <div className="space-y-3">
                    {kids.map((kid, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0">
                            <select
                              value={kid.age}
                              onChange={(e) => updateKidAge(index, parseInt(e.target.value))}
                              className={cn(
                                "rounded-lg border bg-background px-3 py-1.5 text-base h-10 w-[140px]",
                                kidAgeErrors[index] ? "border-destructive" : "border-border"
                              )}
                            >
                              <option value={-1}>Select age</option>
                              <option value={0}>Infant</option>
                              {Array.from({ length: 17 }, (_, i) => (
                                <option key={i + 1} value={i + 1}>{i + 1} {i + 1 === 1 ? "year" : "years"}</option>
                              ))}
                            </select>
                            {kidAgeErrors[index] && (
                              <p className="text-xs text-destructive mt-1">Age is required</p>
                            )}
                          </div>
                          {!showKidNameInputs[index] ? (
                            <button
                              onClick={() => {
                                const newShowInputs = [...showKidNameInputs];
                                newShowInputs[index] = true;
                                setShowKidNameInputs(newShowInputs);
                              }}
                              className="text-xs text-primary underline hover:text-primary/80 mt-2.5"
                            >
                              Add name
                            </button>
                          ) : (
                            <Input
                              value={kid.name}
                              onChange={(e) => updateKidName(index, e.target.value)}
                              placeholder="First name"
                              className="flex-1 h-10 text-base rounded-lg"
                            />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Activities Section */}
      <motion.div
        className={cn(
          "bg-card rounded-2xl border border-border overflow-hidden transition-shadow",
          expandedSection === "activities" ? "card-shadow-lg" : "card-shadow"
        )}
      >
        <button
          onClick={() => setExpandedSection(expandedSection === "activities" ? null : "activities")}
          className="w-full p-4 text-left flex items-center justify-between"
        >
          <span className="text-muted-foreground">Activities</span>
          {expandedSection !== "activities" && (selectedActivities.length > 0 || customActivities.length > 0) && (
            <span className="text-sm font-medium text-foreground">
              {selectedActivities.length + customActivities.length} selected
            </span>
          )}
        </button>
        
        <AnimatePresence>
          {expandedSection === "activities" && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-4">
                <p className="text-sm text-muted-foreground">Select all that apply</p>
                
                <div className="flex flex-wrap gap-2">
                  {activityTags.map(activity => (
                    <button
                      key={activity}
                      onClick={() => toggleActivity(activity)}
                      className={cn(
                        "px-4 py-2 rounded-full text-sm transition-colors",
                        selectedActivities.includes(activity)
                          ? "bg-primary text-primary-foreground"
                          : "bg-accent text-accent-foreground hover:bg-accent/80"
                      )}
                    >
                      {activity}
                    </button>
                  ))}
                  {customActivities.map(activity => (
                    <button
                      key={activity}
                      onClick={() => removeCustomActivity(activity)}
                      className="px-4 py-2 rounded-full text-sm transition-colors bg-primary text-primary-foreground flex items-center gap-1"
                    >
                      {activity}
                      <X className="h-3 w-3" />
                    </button>
                  ))}
                </div>
                
                {/* Add custom activity */}
                <div className="flex gap-2">
                  <Input
                    value={customActivityInput}
                    onChange={(e) => setCustomActivityInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && customActivityInput.trim()) {
                        addCustomActivity(customActivityInput.trim());
                      }
                    }}
                    placeholder="Add another activity..."
                    className="rounded-xl flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      if (customActivityInput.trim()) {
                        addCustomActivity(customActivityInput.trim());
                      }
                    }}
                    className="rounded-full"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>


      {/* Fixed bottom action buttons - always visible outside white boxes */}
      <div className="flex items-center justify-between pt-6 pb-4">
        <button
          onClick={() => {
            setDestinations([]);
            setDateRange(undefined);
            setAdultsData([]);
            setKids([]);
            setSelectedActivities([]);
            setSelectedTransport([]);
            setCustomActivities([]);
            setCustomTransport([]);
            setExpandedSection("where");
          }}
          className="text-sm font-medium underline hover:text-foreground/80 transition-colors"
        >
          Clear all
        </button>
        
        <Button
          onClick={() => {
            if (canSubmit) {
              handleSubmit();
            } else {
              // Validate and show errors
              if (!validateKidAges()) {
                setExpandedSection("who");
                return;
              }
              
              // Navigate to next incomplete section
              if (destinations.length === 0) {
                setExpandedSection("where");
              } else if (!dateRange?.from) {
                setExpandedSection("when");
              } else if (adultsData.length === 0 && kids.length === 0) {
                setExpandedSection("who");
              } else if (selectedActivities.length === 0 && customActivities.length === 0) {
                setExpandedSection("activities");
              }
            }
          }}
          disabled={!canSubmit}
          className={cn(
            "rounded-full px-8",
            canSubmit
              ? "bg-primary hover:bg-primary/90 text-primary-foreground"
              : "bg-muted text-muted-foreground cursor-not-allowed"
          )}
        >
          Generate Packing List
        </Button>
      </div>
    </div>
  );
}
