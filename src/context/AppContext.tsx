// App Context Provider
import { useState, createContext, useContext, ReactNode, useEffect } from 'react';
import { TripInfo, PackingItem, Traveler, ItemCategory } from '@/types/packing';
import { User, AuthState } from '@/types/auth';
import { authApi, tokenManager, tripApi, packingApi, weatherApi, llmApi } from '@/lib/api';
import { Trip, CreateTripRequest, UpdateTripRequest, PackingListForPerson, AddItemRequest, UpdateItemRequest } from '@/types/trip';
import { toast } from '@/hooks/use-toast';
import {
  generateGuestTripId,
  saveGuestTrip,
  getGuestTrip,
  getAllGuestTrips,
  updateGuestTrip,
  deleteGuestTrip,
  isGuestTripId,
  updateGuestTripPackingItems,
  GuestTrip
} from '@/lib/guestStorage';

interface AppState {
  trip: TripInfo | null;
  packingItems: PackingItem[];
  travelers: Traveler[];
  kidMode: boolean;
  hasCompletedOnboarding: boolean;
  auth: AuthState;
  // New trip management state
  trips: Trip[];
  currentTrip: Trip | null;
  isLoadingTrips: boolean;
  tripError: string | null;
}

interface AppContextType extends AppState {
  setTrip: (trip: TripInfo) => void;
  toggleItemPacked: (itemId: string) => Promise<void>;
  toggleItemEssential: (itemId: string) => void;
  setKidMode: (enabled: boolean) => void;
  setHasCompletedOnboarding: (completed: boolean) => void;
  getItemsByPerson: (personId: string) => PackingItem[];
  getEssentialItems: (personId: string) => PackingItem[];
  getPackingProgress: (personId: string) => { packed: number; total: number };
  addItem: (item: Omit<PackingItem, 'id'>) => void;
  updateItem: (itemId: string, updates: Partial<PackingItem>) => void;
  delegateItems: (itemIds: string[], fromPersonId: string, toPersonId: string) => void;
  delegateCategory: (category: ItemCategory, fromPersonId: string, toPersonId: string) => string[];
  getTravelerName: (personId: string) => string;
  moveItemToCategory: (itemId: string, newCategory: ItemCategory) => void;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  // New trip management methods
  loadTrips: () => Promise<void>;
  selectTrip: (tripId: string) => Promise<void>;
  createTrip: (data: CreateTripRequest) => Promise<Trip>;
  updateTrip: (tripId: string, data: UpdateTripRequest) => Promise<Trip>;
  deleteTrip: (tripId: string) => Promise<void>;
  // New packing list methods with API integration
  addPackingItem: (data: Omit<AddItemRequest, 'personId'> & { personId: string }) => Promise<void>;
  updatePackingItem: (itemId: string, data: UpdateItemRequest) => Promise<void>;
  deletePackingItem: (itemId: string) => Promise<void>;
  delegateItem: (itemId: string, toPersonId: string) => Promise<void>;
  addCategory: (personId: string, categoryName: string) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>({
    trip: null,
    packingItems: [],
    travelers: [],
    kidMode: false,
    hasCompletedOnboarding: false,
    auth: {
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    },
    // New trip management state
    trips: [],
    currentTrip: null,
    isLoadingTrips: false,
    tripError: null,
  });

  // Initialize auth state on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Load trips after authentication
  useEffect(() => {
    if (state.auth.isAuthenticated && !state.auth.isLoading) {
      loadTrips();
    }
  }, [state.auth.isAuthenticated, state.auth.isLoading]);

  const setTrip = (trip: TripInfo) => {
    setState(prev => ({ ...prev, trip }));
  };

  const toggleItemPacked = async (itemId: string) => {
    if (!state.currentTrip) {
      console.error('No current trip selected');
      return;
    }

    // Optimistic update
    const previousItems = state.packingItems;
    const updatedItems = state.packingItems.map(item =>
      item.id === itemId ? { ...item, isPacked: !item.isPacked } : item
    );
    
    setState(prev => ({
      ...prev,
      packingItems: updatedItems,
    }));

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: update localStorage
        updateGuestTripPackingItems(state.currentTrip.id, updatedItems);
      } else {
        // Authenticated: update via API
        await packingApi.toggleItemPacked(state.currentTrip.id, itemId);
        // Refresh trip to get updated data
        await selectTrip(state.currentTrip.id);
      }
    } catch (error) {
      console.error('Failed to toggle item packed status:', error);
      // Rollback on error
      setState(prev => ({
        ...prev,
        packingItems: previousItems,
      }));
      toast({
        title: 'Error',
        description: 'Failed to update item status. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const toggleItemEssential = (itemId: string) => {
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item =>
        item.id === itemId ? { ...item, isEssential: !item.isEssential } : item
      ),
    }));
  };

  const setKidMode = (enabled: boolean) => {
    setState(prev => ({ ...prev, kidMode: enabled }));
  };

  const setHasCompletedOnboarding = (completed: boolean) => {
    setState(prev => ({ ...prev, hasCompletedOnboarding: completed }));
  };

  const getItemsByPerson = (personId: string) => {
    return state.packingItems.filter(item => item.personId === personId);
  };

  const getEssentialItems = (personId: string) => {
    return state.packingItems.filter(
      item => item.personId === personId && item.isEssential
    );
  };

  const getPackingProgress = (personId: string) => {
    const items = getItemsByPerson(personId);
    return {
      packed: items.filter(item => item.isPacked).length,
      total: items.length,
    };
  };

  const addItem = (item: Omit<PackingItem, 'id'>) => {
    const newItem: PackingItem = {
      ...item,
      id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    setState(prev => ({
      ...prev,
      packingItems: [...prev.packingItems, newItem],
    }));
  };

  const updateItem = (itemId: string, updates: Partial<PackingItem>) => {
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item =>
        item.id === itemId ? { ...item, ...updates } : item
      ),
    }));
  };


  const getTravelerName = (personId: string): string => {
    const traveler = state.travelers.find(t => t.id === personId);
    if (!traveler) return personId;
    if (traveler.name.includes('Sarah') || personId === 'mom') return 'Mom';
    if (traveler.name.includes('Mike') || personId === 'dad') return 'Dad';
    return traveler.name.split(' ')[0];
  };

  const delegateItems = (itemIds: string[], fromPersonId: string, toPersonId: string) => {
    const fromName = getTravelerName(fromPersonId);
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item => {
        if (itemIds.includes(item.id)) {
          return {
            ...item,
            personId: toPersonId,
            delegationInfo: {
              fromPersonId,
              fromPersonName: fromName,
              delegatedAt: new Date().toISOString(),
            },
          };
        }
        return item;
      }),
    }));
  };

  const delegateCategory = (category: ItemCategory, fromPersonId: string, toPersonId: string): string[] => {
    const itemsToDelegate = state.packingItems.filter(
      item => item.personId === fromPersonId && item.category === category
    );
    const itemIds = itemsToDelegate.map(item => item.id);
    delegateItems(itemIds, fromPersonId, toPersonId);
    return itemIds;
  };

  const moveItemToCategory = (itemId: string, newCategory: ItemCategory) => {
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item =>
        item.id === itemId ? { ...item, category: newCategory } : item
      ),
    }));
  };

  // Authentication methods
  const login = () => {
    authApi.loginWithGoogle();
  };

  const logout = async () => {
    setState(prev => ({
      ...prev,
      auth: {
        ...prev.auth,
        isLoading: true,
        error: null,
      },
    }));

    try {
      await authApi.logout();
      setState(prev => ({
        ...prev,
        auth: {
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        },
        // Clear trip data on logout
        trip: null,
        packingItems: [],
        travelers: [],
        hasCompletedOnboarding: false,
      }));
    } catch (error) {
      console.error('Logout failed:', error);
      setState(prev => ({
        ...prev,
        auth: {
          ...prev.auth,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Logout failed',
        },
      }));
    }
  };

  const checkAuth = async () => {
    // Check if we have a token
    if (!tokenManager.hasValidToken()) {
      setState(prev => ({
        ...prev,
        auth: {
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        },
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      auth: {
        ...prev.auth,
        isLoading: true,
        error: null,
      },
    }));

    try {
      const user = await authApi.getCurrentUser();
      setState(prev => ({
        ...prev,
        auth: {
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        },
      }));
    } catch (error) {
      console.error('Auth check failed:', error);
      // Clear invalid tokens
      tokenManager.clearTokens();
      setState(prev => ({
        ...prev,
        auth: {
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Authentication failed',
        },
      }));
    }
  };

  // Trip Management Methods
  
  /**
   * Helper function to flatten packing lists from backend format to frontend format
   */
  const flattenPackingLists = (packingLists: PackingListForPerson[]): PackingItem[] => {
    return packingLists.flatMap(list =>
      list.items.map(item => ({
        ...item,
        personId: list.personId,
      }))
    );
  };

  /**
   * Helper function to convert Trip to TripInfo for backward compatibility
   */
  const convertTripToTripInfo = (trip: Trip): TripInfo => {
    if (!trip.weatherData) {
      throw new Error('Trip weather data is missing. Cannot display trip without weather information.');
    }
    
    return {
      id: trip.id,
      destination: trip.destination,
      startDate: trip.startDate,
      endDate: trip.endDate,
      duration: trip.duration,
      weather: trip.weatherData,
      travelers: trip.travelers.map(t => ({
        id: t.id,
        name: t.name,
        age: t.age,
        type: t.type,
        avatar: t.avatar,
      })),
      createdAt: trip.createdAt,
      activities: trip.activities || [],
    };
  };

  const loadTrips = async () => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      let trips: Trip[] = [];
      
      if (state.auth.isAuthenticated) {
        // Load trips from API
        const response = await tripApi.getTrips();
        trips = response.trips;
      } else {
        // Load guest trips from localStorage
        trips = getAllGuestTrips();
      }
      
      setState(prev => ({
        ...prev,
        trips,
        isLoadingTrips: false,
        tripError: null,
      }));
    } catch (error) {
      console.error('Failed to load trips:', error);
      setState(prev => ({
        ...prev,
        isLoadingTrips: false,
        tripError: error instanceof Error ? error.message : 'Failed to load trips',
      }));
    }
  };

  const selectTrip = async (tripId: string) => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      let trip: Trip;
      
      if (isGuestTripId(tripId)) {
        // Load guest trip from localStorage
        const guestTrip = getGuestTrip(tripId);
        if (!guestTrip) {
          throw new Error('Guest trip not found');
        }
        trip = guestTrip;
      } else {
        // Load trip from API
        trip = await tripApi.getTrip(tripId);
      }
      
      // Convert to legacy format for backward compatibility
      const tripInfo = convertTripToTripInfo(trip);
      const packingItems = flattenPackingLists(trip.packingLists);
      
      setState(prev => ({
        ...prev,
        currentTrip: trip,
        trip: tripInfo,
        packingItems,
        travelers: trip.travelers,
        isLoadingTrips: false,
        tripError: null,
        hasCompletedOnboarding: true,
      }));
    } catch (error) {
      console.error('Failed to select trip:', error);
      setState(prev => ({
        ...prev,
        isLoadingTrips: false,
        tripError: error instanceof Error ? error.message : 'Failed to load trip',
      }));
    }
  };

  const createTrip = async (data: CreateTripRequest): Promise<Trip> => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      let trip: Trip | GuestTrip;
      
      // Check if user is authenticated
      if (state.auth.isAuthenticated) {
        // Authenticated: create trip via API
        trip = await tripApi.createTrip(data);
      } else {
        // Guest mode: create trip locally with real weather data
        const guestTripId = generateGuestTripId();
        
        // Calculate duration
        const start = new Date(data.startDate);
        const end = new Date(data.endDate);
        const durationDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
        
        // Fetch real weather data for guest mode
        const weatherResponse = await weatherApi.getForecast(
          data.destination,
          data.startDate,
          data.endDate
        );
        
        const weatherData = {
          avgTemp: weatherResponse.avgTemp,
          tempUnit: weatherResponse.tempUnit as 'C' | 'F',
          conditions: weatherResponse.conditions as ('sunny' | 'rainy' | 'snowy' | 'cloudy' | 'mixed')[],
          recommendation: weatherResponse.recommendation,
        };
        
        // Prepare travelers with IDs and avatars
        const travelers = data.travelers.map((t, idx) => {
          // Assign emoji avatars based on traveler type and index
          let avatar = '👤'; // default adult
          if (t.type === 'adult') {
            avatar = idx === 0 ? '👩' : '👨'; // First adult is mom, second is dad
          } else if (t.type === 'child') {
            // Alternate between girl and boy emojis for children
            avatar = idx % 2 === 0 ? '👧' : '👦';
          } else if (t.type === 'infant') {
            avatar = '👶';
          }
          
          return {
            ...t,
            id: `guest-traveler-${idx}`,
            avatar,
          };
        });
        
        // Generate context-aware packing lists using LLM
        console.log('Generating packing list with LLM for guest trip...');
        console.log('🔍 DEBUG - Activities being sent to LLM:', data.activities);
        console.log('🔍 DEBUG - Full request data:', {
          destination: data.destination,
          startDate: data.startDate,
          endDate: data.endDate,
          activities: data.activities || [],
          transport: data.transport || [],
          travelers: travelers.map(t => ({ id: t.id, name: t.name, type: t.type })),
        });
        console.log('🔍 DEBUG - About to call LLM API with:', {
          destination: data.destination,
          startDate: data.startDate,
          endDate: data.endDate,
          activities: data.activities || [],
          transport: data.transport || [],
          travelerCount: travelers.length
        });
        
        const llmItems = await llmApi.generatePackingList({
          destination: data.destination,
          startDate: data.startDate,
          endDate: data.endDate,
          activities: data.activities || [],
          transport: data.transport || [],
          weather: weatherData,
          travelers: travelers,
        });
        
        console.log('🔍 DEBUG - LLM API call completed');
        console.log('🔍 DEBUG - LLM returned items:', llmItems);
        console.log('🔍 DEBUG - Number of items:', llmItems ? llmItems.length : 'llmItems is null/undefined');
        console.log('🔍 DEBUG - Sample item:', llmItems && llmItems.length > 0 ? llmItems[0] : 'No items');
        
        // Group items by person to create packing lists
        const itemsByPerson = new Map<string, PackingItem[]>();
        llmItems.forEach(item => {
          console.log('🔍 DEBUG - Processing item:', item.name, 'for person:', item.personId);
          if (!itemsByPerson.has(item.personId)) {
            itemsByPerson.set(item.personId, []);
          }
          itemsByPerson.get(item.personId)!.push(item);
        });
        
        console.log('🔍 DEBUG - Items grouped by person:', Array.from(itemsByPerson.entries()).map(([id, items]) => ({ id, count: items.length })));
        
        // Create packing lists from grouped items
        const packingLists = travelers.map(traveler => {
          const items = itemsByPerson.get(traveler.id) || [];
          const categories = [...new Set(items.map(item => item.category))];
          
          console.log(`🔍 DEBUG - Creating packing list for ${traveler.name}:`, {
            travelerId: traveler.id,
            itemCount: items.length,
            categories: categories
          });
          
          return {
            personId: traveler.id,
            personName: traveler.name,
            categories: categories.length > 0 ? categories : ['clothing', 'toiletries', 'electronics', 'misc'],
            items: items,
          };
        });
        
        console.log('🔍 DEBUG - Final packingLists structure:', packingLists.map(pl => ({
          personName: pl.personName,
          personId: pl.personId,
          itemCount: pl.items.length,
          categories: pl.categories
        })));
        
        console.log('Successfully generated LLM-based packing lists for guest trip');
        
        // Create guest trip with LLM-generated packing lists
        const guestTrip: GuestTrip = {
          id: guestTripId,
          userId: 'guest',
          destination: data.destination,
          startDate: data.startDate,
          endDate: data.endDate,
          duration: durationDays,
          travelers: travelers,
          activities: data.activities || [],
          transport: data.transport || [],
          packingLists: packingLists,
          weatherData,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          isGuestMode: true,
        };
        
        // Save to localStorage
        saveGuestTrip(guestTrip);
        trip = guestTrip;
      }
        
      // Convert to legacy format for backward compatibility
      const tripInfo = convertTripToTripInfo(trip);
      const packingItems = flattenPackingLists(trip.packingLists);
      
      setState(prev => ({
        ...prev,
        trips: [...prev.trips, trip],
        currentTrip: trip,
        trip: tripInfo,
        packingItems,
        travelers: trip.travelers,
        isLoadingTrips: false,
        tripError: null,
        hasCompletedOnboarding: true,
      }));
      
      return trip;
    } catch (error) {
      console.error('Failed to create trip:', error);
      setState(prev => ({
        ...prev,
        isLoadingTrips: false,
        tripError: error instanceof Error ? error.message : 'Failed to create trip',
      }));
      throw error;
    }
  };
  

  const updateTrip = async (tripId: string, data: UpdateTripRequest): Promise<Trip> => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      const trip = await tripApi.updateTrip(tripId, data);
      
      // Convert to legacy format for backward compatibility
      const tripInfo = convertTripToTripInfo(trip);
      const packingItems = flattenPackingLists(trip.packingLists);
      
      setState(prev => ({
        ...prev,
        trips: prev.trips.map(t => (t.id === tripId ? trip : t)),
        currentTrip: trip,
        trip: tripInfo,
        packingItems,
        travelers: trip.travelers,
        isLoadingTrips: false,
        tripError: null,
      }));
      
      return trip;
    } catch (error) {
      console.error('Failed to update trip:', error);
      setState(prev => ({
        ...prev,
        isLoadingTrips: false,
        tripError: error instanceof Error ? error.message : 'Failed to update trip',
      }));
      throw error;
    }
  };

  const deleteTrip = async (tripId: string): Promise<void> => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      await tripApi.deleteTrip(tripId);
      
      setState(prev => {
        const newTrips = prev.trips.filter(t => t.id !== tripId);
        const wasCurrentTrip = prev.currentTrip?.id === tripId;
        
        return {
          ...prev,
          trips: newTrips,
          currentTrip: wasCurrentTrip ? null : prev.currentTrip,
          trip: wasCurrentTrip ? null : prev.trip,
          packingItems: wasCurrentTrip ? [] : prev.packingItems,
          travelers: wasCurrentTrip ? [] : prev.travelers,
          isLoadingTrips: false,
          tripError: null,
        };
      });
    } catch (error) {
      console.error('Failed to delete trip:', error);
      setState(prev => ({
        ...prev,
        isLoadingTrips: false,
        tripError: error instanceof Error ? error.message : 'Failed to delete trip',
      }));
      throw error;
    }
  };

  // Packing List Methods with API Integration

  const addPackingItem = async (data: Omit<AddItemRequest, 'personId'> & { personId: string }): Promise<void> => {
    if (!state.currentTrip) {
      toast({
        title: 'Error',
        description: 'No trip selected',
        variant: 'destructive',
      });
      return;
    }

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: add item locally
        const newItem: PackingItem = {
          id: `guest-item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          name: data.name,
          emoji: data.emoji || '📦',
          quantity: data.quantity || 1,
          category: data.category,
          isPacked: false,
          isEssential: data.isEssential || false,
          visibleToKid: true,
          personId: data.personId,
          notes: data.notes,
        };
        
        const updatedItems = [...state.packingItems, newItem];
        setState(prev => ({
          ...prev,
          packingItems: updatedItems,
        }));
        
        // Update localStorage
        updateGuestTripPackingItems(state.currentTrip.id, updatedItems);
        
        toast({
          title: 'Success',
          description: 'Item added successfully',
        });
      } else {
        // Authenticated: add via API
        const newItem = await packingApi.addPackingItem(state.currentTrip.id, data);
        
        // Add to local state
        setState(prev => ({
          ...prev,
          packingItems: [...prev.packingItems, newItem],
        }));

        toast({
          title: 'Success',
          description: 'Item added successfully',
        });

        // Refresh trip to ensure consistency
        await selectTrip(state.currentTrip.id);
      }
    } catch (error) {
      console.error('Failed to add packing item:', error);
      toast({
        title: 'Error',
        description: 'Failed to add item. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const updatePackingItem = async (itemId: string, data: UpdateItemRequest): Promise<void> => {
    if (!state.currentTrip) {
      toast({
        title: 'Error',
        description: 'No trip selected',
        variant: 'destructive',
      });
      return;
    }

    // Optimistic update
    const previousItems = state.packingItems;
    const updatedItems = state.packingItems.map(item =>
      item.id === itemId ? { ...item, ...data } : item
    );
    
    setState(prev => ({
      ...prev,
      packingItems: updatedItems,
    }));

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: update localStorage
        updateGuestTripPackingItems(state.currentTrip.id, updatedItems);
        
        toast({
          title: 'Success',
          description: 'Item updated successfully',
        });
      } else {
        // Authenticated: update via API
        await packingApi.updatePackingItem(state.currentTrip.id, itemId, data);
        
        toast({
          title: 'Success',
          description: 'Item updated successfully',
        });

        // Refresh trip to ensure consistency
        await selectTrip(state.currentTrip.id);
      }
    } catch (error) {
      console.error('Failed to update packing item:', error);
      // Rollback on error
      setState(prev => ({
        ...prev,
        packingItems: previousItems,
      }));
      toast({
        title: 'Error',
        description: 'Failed to update item. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const deletePackingItem = async (itemId: string): Promise<void> => {
    if (!state.currentTrip) {
      toast({
        title: 'Error',
        description: 'No trip selected',
        variant: 'destructive',
      });
      return;
    }

    // Optimistic update
    const previousItems = state.packingItems;
    const updatedItems = state.packingItems.filter(item => item.id !== itemId);
    
    setState(prev => ({
      ...prev,
      packingItems: updatedItems,
    }));

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: update localStorage
        updateGuestTripPackingItems(state.currentTrip.id, updatedItems);
        
        toast({
          title: 'Success',
          description: 'Item deleted successfully',
        });
      } else {
        // Authenticated: delete via API
        await packingApi.deletePackingItem(state.currentTrip.id, itemId);
        
        toast({
          title: 'Success',
          description: 'Item deleted successfully',
        });
      }
    } catch (error) {
      console.error('Failed to delete packing item:', error);
      // Rollback on error
      setState(prev => ({
        ...prev,
        packingItems: previousItems,
      }));
      toast({
        title: 'Error',
        description: 'Failed to delete item. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const delegateItem = async (itemId: string, toPersonId: string): Promise<void> => {
    if (!state.currentTrip) {
      toast({
        title: 'Error',
        description: 'No trip selected',
        variant: 'destructive',
      });
      return;
    }

    // Find the item to get fromPersonId
    const item = state.packingItems.find(i => i.id === itemId);
    if (!item) {
      toast({
        title: 'Error',
        description: 'Item not found',
        variant: 'destructive',
      });
      return;
    }

    const fromPersonId = item.personId;

    // Optimistic update
    const previousItems = state.packingItems;
    const fromName = getTravelerName(fromPersonId);
    const updatedItems = state.packingItems.map(i =>
      i.id === itemId
        ? {
            ...i,
            personId: toPersonId,
            delegationInfo: {
              fromPersonId,
              fromPersonName: fromName,
              delegatedAt: new Date().toISOString(),
            },
          }
        : i
    );
    
    setState(prev => ({
      ...prev,
      packingItems: updatedItems,
    }));

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: update localStorage
        updateGuestTripPackingItems(state.currentTrip.id, updatedItems);
        
        toast({
          title: 'Success',
          description: 'Item delegated successfully',
        });
      } else {
        // Authenticated: delegate via API
        await packingApi.delegateItem(state.currentTrip.id, itemId, fromPersonId, toPersonId);
        
        toast({
          title: 'Success',
          description: 'Item delegated successfully',
        });

        // Refresh trip to ensure consistency
        await selectTrip(state.currentTrip.id);
      }
    } catch (error) {
      console.error('Failed to delegate item:', error);
      // Rollback on error
      setState(prev => ({
        ...prev,
        packingItems: previousItems,
      }));
      toast({
        title: 'Error',
        description: 'Failed to delegate item. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const addCategory = async (personId: string, categoryName: string): Promise<void> => {
    if (!state.currentTrip) {
      toast({
        title: 'Error',
        description: 'No trip selected',
        variant: 'destructive',
      });
      return;
    }

    try {
      if (isGuestTripId(state.currentTrip.id)) {
        // Guest mode: categories are managed locally, just show success
        // In guest mode, categories are dynamically derived from items
        toast({
          title: 'Success',
          description: 'Category added successfully',
        });
      } else {
        // Authenticated: add via API
        await packingApi.addCategory(state.currentTrip.id, personId, categoryName);
        
        toast({
          title: 'Success',
          description: 'Category added successfully',
        });

        // Refresh trip to ensure consistency
        await selectTrip(state.currentTrip.id);
      }
    } catch (error) {
      console.error('Failed to add category:', error);
      toast({
        title: 'Error',
        description: 'Failed to add category. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  return (
    <AppContext.Provider
      value={{
        ...state,
        setTrip,
        toggleItemPacked,
        toggleItemEssential,
        setKidMode,
        setHasCompletedOnboarding,
        getItemsByPerson,
        getEssentialItems,
        getPackingProgress,
        addItem,
        updateItem,
        delegateItems,
        delegateCategory,
        getTravelerName,
        moveItemToCategory,
        login,
        logout,
        checkAuth,
        loadTrips,
        selectTrip,
        createTrip,
        updateTrip,
        deleteTrip,
        addPackingItem,
        updatePackingItem,
        deletePackingItem,
        delegateItem,
        addCategory,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
