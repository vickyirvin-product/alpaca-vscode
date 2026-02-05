// App Context Provider
import { useState, createContext, useContext, ReactNode, useEffect } from 'react';
import { TripInfo, PackingItem, Traveler, ItemCategory } from '@/types/packing';
import { mockTrip, mockPackingItems, mockTravelers } from '@/data/mockData';
import { User, AuthState } from '@/types/auth';
import { authApi, tokenManager, tripApi, packingApi } from '@/lib/api';
import { Trip, CreateTripRequest, UpdateTripRequest, PackingListForPerson, AddItemRequest, UpdateItemRequest } from '@/types/trip';
import { toast } from '@/hooks/use-toast';

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
  resetToMockData: () => void;
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
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item =>
        item.id === itemId ? { ...item, isPacked: !item.isPacked } : item
      ),
    }));

    try {
      await packingApi.toggleItemPacked(state.currentTrip.id, itemId);
      // Refresh trip to get updated data
      await selectTrip(state.currentTrip.id);
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

  const resetToMockData = () => {
    setState(prev => ({
      ...prev,
      trip: mockTrip,
      packingItems: mockPackingItems,
      travelers: mockTravelers,
      kidMode: false,
      hasCompletedOnboarding: true,
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
    return {
      id: trip.id,
      destination: trip.destination,
      startDate: trip.startDate,
      endDate: trip.endDate,
      duration: trip.duration,
      weather: trip.weatherData || {
        avgTemp: 20,
        tempUnit: 'C',
        conditions: ['sunny'],
        recommendation: 'Pack light clothing',
      },
      travelers: trip.travelers.map(t => ({
        id: t.id,
        name: t.name,
        age: t.age,
        type: t.type,
        avatar: t.avatar,
      })),
      createdAt: trip.createdAt,
    };
  };

  const loadTrips = async () => {
    setState(prev => ({ ...prev, isLoadingTrips: true, tripError: null }));

    try {
      const response = await tripApi.getTrips();
      setState(prev => ({
        ...prev,
        trips: response.trips,
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
      const trip = await tripApi.getTrip(tripId);
      
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
      const trip = await tripApi.createTrip(data);
      
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
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(item =>
        item.id === itemId ? { ...item, ...data } : item
      ),
    }));

    try {
      await packingApi.updatePackingItem(state.currentTrip.id, itemId, data);
      
      toast({
        title: 'Success',
        description: 'Item updated successfully',
      });

      // Refresh trip to ensure consistency
      await selectTrip(state.currentTrip.id);
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
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.filter(item => item.id !== itemId),
    }));

    try {
      await packingApi.deletePackingItem(state.currentTrip.id, itemId);
      
      toast({
        title: 'Success',
        description: 'Item deleted successfully',
      });
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
    setState(prev => ({
      ...prev,
      packingItems: prev.packingItems.map(i =>
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
      ),
    }));

    try {
      await packingApi.delegateItem(state.currentTrip.id, itemId, fromPersonId, toPersonId);
      
      toast({
        title: 'Success',
        description: 'Item delegated successfully',
      });

      // Refresh trip to ensure consistency
      await selectTrip(state.currentTrip.id);
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
      await packingApi.addCategory(state.currentTrip.id, personId, categoryName);
      
      toast({
        title: 'Success',
        description: 'Category added successfully',
      });

      // Refresh trip to ensure consistency
      await selectTrip(state.currentTrip.id);
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
        resetToMockData,
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
