import { useState, useEffect, useRef, useCallback } from "react";
import { Search, MapPin, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { AutocompleteResponse, PlaceSuggestion } from "@/types/maps";

interface LocationAutocompleteProps {
  value: string;
  onChange: (location: string, placeId?: string) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export function LocationAutocomplete({
  value,
  onChange,
  placeholder = "Search destinations",
  className,
  autoFocus = false,
}: LocationAutocompleteProps) {
  const [inputValue, setInputValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Sync with external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch suggestions from API
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log("Fetching suggestions for query:", query);
      const response = await api.get<AutocompleteResponse>(
        `/api/v1/maps/autocomplete?input=${encodeURIComponent(query)}`
      );
      
      console.log("Raw API response:", response);
      console.log("Response type:", typeof response);
      console.log("Response keys:", Object.keys(response || {}));
      console.log("Suggestions:", response?.suggestions);
      console.log("Suggestions length:", response?.suggestions?.length);
      
      const suggestions = response?.suggestions || [];
      console.log("Setting suggestions:", suggestions);
      setSuggestions(suggestions);
      setIsOpen(suggestions.length > 0);
      setSelectedIndex(-1);
      
      console.log("isOpen set to:", suggestions.length > 0);
    } catch (err) {
      console.error("Failed to fetch location suggestions:", err);
      console.error("Error details:", err);
      setError("Failed to load suggestions");
      setSuggestions([]);
      setIsOpen(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Debounced input handler
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      fetchSuggestions(newValue);
    }, 400);
  };

  // Handle suggestion selection
  const handleSelectSuggestion = (suggestion: PlaceSuggestion) => {
    // Clear the input value to allow for next location entry
    setInputValue("");
    onChange(suggestion.description, suggestion.placeId);
    setIsOpen(false);
    setSuggestions([]);
    setSelectedIndex(-1);
    
    // Keep focus on input for next entry
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === "Enter" && inputValue.trim()) {
        // Allow manual entry on Enter
        onChange(inputValue.trim());
        setIsOpen(false);
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        } else if (inputValue.trim()) {
          onChange(inputValue.trim());
          setIsOpen(false);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  return (
    <div ref={wrapperRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              setIsOpen(true);
            }
          }}
          placeholder={placeholder}
          className="pl-10 pr-10 rounded-xl"
          autoFocus={autoFocus}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground animate-spin" />
        )}
      </div>

      {/* Suggestions dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-popover border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="max-h-[300px] overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <button
                key={suggestion.placeId}
                onClick={() => handleSelectSuggestion(suggestion)}
                className={cn(
                  "w-full px-4 py-3 text-left hover:bg-accent transition-colors flex items-start gap-3",
                  selectedIndex === index && "bg-accent"
                )}
              >
                <MapPin className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">
                    {suggestion.mainText}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {suggestion.secondaryText}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute z-50 w-full mt-2 bg-destructive/10 border border-destructive/20 rounded-xl p-3">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  );
}