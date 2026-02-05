# Frontend Integration Plan

This document outlines the strategy for connecting the React/TypeScript frontend to the FastAPI backend.

## 1. Architecture Overview

### Current vs. Target State

| Feature | Current State (Mock) | Target State (Integrated) |
| :--- | :--- | :--- |
| **Data Source** | `src/data/mockData.ts` | Backend API (`http://localhost:8000`) |
| **State Management** | `AppContext.tsx` (Local State) | `AppContext.tsx` + `React Query` (Async State) |
| **Authentication** | None (Auto-logged in as "Mom") | Google OAuth + JWT (Access/Refresh Tokens) |
| **IDs** | Simple strings (e.g., 'trip-001') | MongoDB ObjectIds (24-char hex strings) |
| **Data Format** | camelCase | Backend uses snake_case (requires adaptation) |

### Key Structural Differences

1.  **Packing Items:**
    *   **Frontend:** Flat array of all items (`PackingItem[]`), filtered by `personId`.
    *   **Backend:** Grouped by person (`packing_lists: [{ person_id: "...", items: [...] }]`).
    *   **Strategy:** The frontend `AppContext` fetching logic will need to "flatten" the backend response to maintain compatibility with existing components, OR refactor components to accept grouped data. *Recommendation: Flatten in the API adapter layer to minimize component churn.*

2.  **Field Naming:**
    *   **Frontend:** `isPacked`, `personId`, `firstName` (camelCase)
    *   **Backend:** `is_packed`, `person_id`, `first_name` (snake_case)
    *   **Strategy:** Implement robust CamelToSnake and SnakeToCamel transformers in `src/lib/api.ts`.

## 2. Integration Checklist

### Phase 1: Authentication & Core API Setup
- [ ] **Update `src/lib/api.ts`**
    - [ ] Add interceptors for JWT token injection.
    - [ ] Add 401 response handling (auto-logout/refresh).
    - [ ] Implement `snake_case` <-> `camelCase` transformation utilities.
- [ ] **Create `AuthContext.tsx`** (or enhance `AppContext`)
    - [ ] Store `user` object and `isAuthenticated` state.
    - [ ] Implement `login()` (redirect to Google) and `logout()` functions.
    - [ ] Handle OAuth callback route (`/auth/callback`).

### Phase 2: Trip Management (Onboarding)
- [ ] **Update `src/types/packing.ts`**
    - [ ] Align `TripInfo` interfaces with backend `TripResponse` (handling the `weather` vs `weather_data` naming).
- [ ] **Refactor `SmartWizard.tsx` / `StructuredTripForm.tsx`**
    - [ ] Replace `setTrip` with `api.post('/api/v1/trips', ...)`
    - [ ] Handle loading states during AI generation.
- [ ] **Update `AppContext.tsx` - `setTrip`**
    - [ ] Fetch trip details from `/api/v1/trips/{id}` upon selection.

### Phase 3: Packing List Interactions
- [ ] **Update `AppContext.tsx` - Data Fetching**
    - [ ] Fetch trip includes packing lists. Flatten `trip.packing_lists` into `state.packingItems`.
- [ ] **Update `AppContext.tsx` - Item Actions**
    - [ ] `toggleItemPacked` -> `PUT /api/v1/trips/{id}/items/{itemId}/toggle-packed`
    - [ ] `addItem` -> `POST /api/v1/trips/{id}/items`
    - [ ] `updateItem` -> `PUT /api/v1/trips/{id}/items/{itemId}`
    - [ ] `deleteItem` -> `DELETE /api/v1/trips/{id}/items/{itemId}`
    - [ ] `delegateItems` -> `POST .../delegate`

### Phase 4: Collaboration & Maps
- [ ] **Integrate Nudges**
    - [ ] Create UI for sending nudges (using `POST /api/v1/trips/{id}/nudges`).
- [ ] **Integrate Sharing**
    - [ ] Update "Share" button to call `POST /api/v1/trips/{id}/share`.
- [ ] **Integrate Google Places Autocomplete**
    - [ ] Connect Location input in Onboarding to `/api/v1/maps/autocomplete`.

## 3. Data Mapping & Transformation

### Adapter Pattern Example

```typescript
// src/lib/adapters.ts

export const adaptBackendTripToFrontend = (backendTrip: any): TripInfo => ({
  id: backendTrip.id,
  destination: backendTrip.destination,
  startDate: backendTrip.start_date,
  endDate: backendTrip.end_date,
  duration: backendTrip.duration,
  weather: backendTrip.weather_data ? {
    avgTemp: backendTrip.weather_data.avg_temp,
    tempUnit: backendTrip.weather_data.temp_unit,
    conditions: backendTrip.weather_data.conditions,
    recommendation: backendTrip.weather_data.recommendation
  } : undefined,
  travelers: backendTrip.travelers.map(t => ({
    id: t.id,
    name: t.name,
    age: t.age,
    type: t.type,
    avatar: t.avatar
  })),
  createdAt: backendTrip.created_at
});

export const flattenPackingLists = (packingLists: any[]): PackingItem[] => {
  return packingLists.flatMap(list => 
    list.items.map(item => ({
      id: item.id,
      personId: list.person_id, // Important: Map the list owner to the item
      name: item.name,
      category: item.category,
      quantity: item.quantity,
      isPacked: item.is_packed,
      isEssential: item.is_essential,
      visibleToKid: item.visible_to_kid,
      emoji: item.emoji
    }))
  );
};
```

## 4. API Endpoint Mapping

| Action | Frontend Needs | Backend Endpoint | Request Body |
| :--- | :--- | :--- | :--- |
| **Create Trip** | Trip details | `POST /api/v1/trips` | `TripCreate` |
| **Get Trip** | Trip ID | `GET /api/v1/trips/{id}` | - |
| **Add Item** | Item details | `POST .../items` | `AddItemRequest` |
| **Toggle Pack**| Item ID | `PUT .../items/{id}/toggle-packed` | - |
| **Edit Item** | Updates | `PUT .../items/{id}` | `UpdateItemRequest` |
| **Delete Item**| Item ID | `DELETE .../items/{id}` | - |
| **Delegate** | From/To IDs | `POST .../items/{id}/delegate` | `DelegateItemRequest` |

## 5. Potential Challenges & Mitigations

1.  **Optimistic UI Updates:**
    *   **Challenge:** Waiting for server response for every checkbox click feels slow.
    *   **Mitigation:** Implement optimistic updates in `AppContext`. Update local state immediately, then revert if API call fails.

2.  **Authentication Persistence:**
    *   **Challenge:** Handling token expiration while the user is editing a list.
    *   **Mitigation:** Implement a silent refresh mechanism in the API interceptor. Save trip state to local storage as backup.

3.  **Snake Case vs Camel Case:**
    *   **Challenge:** Inconsistent casing leads to "undefined" errors.
    *   **Mitigation:** Use strict TypeScript interfaces for API responses (e.g., `TripResponse` vs `TripInfo`) and use the adapter functions defined above. Do not cast `any`.

## 6. Implementation Order

1.  **Authentication:** Set up the "front door" first.
2.  **Adapters:** Build the translation layer.
3.  **Onboarding:** Allow creating real data.
4.  **Dashboard/Packing:** Display and interact with real data.