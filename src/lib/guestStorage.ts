// Guest mode storage utilities for managing trips without authentication

import { Trip, CreateTripRequest } from '@/types/trip';
import { PackingItem } from '@/types/packing';

const GUEST_TRIP_PREFIX = 'alpaca_guest_trip_';
const GUEST_TRIP_LIST_KEY = 'alpaca_guest_trips';

export interface GuestTrip extends Trip {
  isGuestMode: true;
}

/**
 * Generate a unique guest trip ID
 */
export function generateGuestTripId(): string {
  return `guest-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Save a guest trip to localStorage
 */
export function saveGuestTrip(trip: GuestTrip): void {
  try {
    const key = `${GUEST_TRIP_PREFIX}${trip.id}`;
    localStorage.setItem(key, JSON.stringify(trip));
    
    // Update the list of guest trip IDs
    const tripList = getGuestTripIds();
    if (!tripList.includes(trip.id)) {
      tripList.push(trip.id);
      localStorage.setItem(GUEST_TRIP_LIST_KEY, JSON.stringify(tripList));
    }
  } catch (error) {
    console.error('Failed to save guest trip:', error);
    throw new Error('Failed to save trip locally');
  }
}

/**
 * Get a guest trip from localStorage
 */
export function getGuestTrip(tripId: string): GuestTrip | null {
  try {
    const key = `${GUEST_TRIP_PREFIX}${tripId}`;
    const data = localStorage.getItem(key);
    if (!data) return null;
    return JSON.parse(data) as GuestTrip;
  } catch (error) {
    console.error('Failed to load guest trip:', error);
    return null;
  }
}

/**
 * Get all guest trip IDs
 */
export function getGuestTripIds(): string[] {
  try {
    const data = localStorage.getItem(GUEST_TRIP_LIST_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Failed to load guest trip list:', error);
    return [];
  }
}

/**
 * Get all guest trips
 */
export function getAllGuestTrips(): GuestTrip[] {
  const tripIds = getGuestTripIds();
  return tripIds
    .map(id => getGuestTrip(id))
    .filter((trip): trip is GuestTrip => trip !== null);
}

/**
 * Delete a guest trip from localStorage
 */
export function deleteGuestTrip(tripId: string): void {
  try {
    const key = `${GUEST_TRIP_PREFIX}${tripId}`;
    localStorage.removeItem(key);
    
    // Update the list of guest trip IDs
    const tripList = getGuestTripIds();
    const updatedList = tripList.filter(id => id !== tripId);
    localStorage.setItem(GUEST_TRIP_LIST_KEY, JSON.stringify(updatedList));
  } catch (error) {
    console.error('Failed to delete guest trip:', error);
  }
}

/**
 * Update a guest trip in localStorage
 */
export function updateGuestTrip(tripId: string, updates: Partial<GuestTrip>): GuestTrip | null {
  try {
    const trip = getGuestTrip(tripId);
    if (!trip) return null;
    
    const updatedTrip: GuestTrip = {
      ...trip,
      ...updates,
      id: tripId, // Ensure ID doesn't change
      isGuestMode: true, // Ensure guest mode flag stays
    };
    
    saveGuestTrip(updatedTrip);
    return updatedTrip;
  } catch (error) {
    console.error('Failed to update guest trip:', error);
    return null;
  }
}

/**
 * Clear all guest trips from localStorage
 */
export function clearAllGuestTrips(): void {
  try {
    const tripIds = getGuestTripIds();
    tripIds.forEach(id => {
      const key = `${GUEST_TRIP_PREFIX}${id}`;
      localStorage.removeItem(key);
    });
    localStorage.removeItem(GUEST_TRIP_LIST_KEY);
  } catch (error) {
    console.error('Failed to clear guest trips:', error);
  }
}

/**
 * Check if a trip ID is a guest trip
 */
export function isGuestTripId(tripId: string): boolean {
  return tripId.startsWith('guest-');
}

/**
 * Update packing items for a guest trip
 */
export function updateGuestTripPackingItems(tripId: string, items: PackingItem[]): boolean {
  try {
    const trip = getGuestTrip(tripId);
    if (!trip) return false;
    
    // Group items by personId to update packing lists
    const itemsByPerson = items.reduce((acc, item) => {
      if (!acc[item.personId]) {
        acc[item.personId] = [];
      }
      acc[item.personId].push(item);
      return acc;
    }, {} as Record<string, PackingItem[]>);
    
    // Update packing lists
    const updatedPackingLists = trip.packingLists.map(list => ({
      ...list,
      items: itemsByPerson[list.personId] || [],
    }));
    
    updateGuestTrip(tripId, { packingLists: updatedPackingLists });
    return true;
  } catch (error) {
    console.error('Failed to update guest trip packing items:', error);
    return false;
  }
}