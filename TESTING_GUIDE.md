# Integration Testing Guide

This guide provides comprehensive instructions for testing the Alpaca For You application with the fully integrated frontend and backend.

## Prerequisites

Before starting, ensure all systems are running and configured:

1.  **Backend Server**:
    *   Running on `http://localhost:8000`
    *   MongoDB connection active
    *   `.env` file configured with Google OAuth credentials
    *   Verify: Open `http://localhost:8000/healthz` (Should return `{"status":"ok"}`)

2.  **Frontend Server**:
    *   Running on `http://localhost:5173` (or `8080`)
    *   Connected to backend via proxy or CORS
    *   Verify: Open `http://localhost:5173` (Should redirect to `/login`)

3.  **Browser**:
    *   Chrome or modern browser recommended
    *   DevTools open (F12) for monitoring network requests

## Test Scenarios

### 1. Authentication Flow

**Goal**: Verify users can securely log in and maintain a session.

| Step | Action | Expected Outcome |
| :--- | :--- | :--- |
| 1 | Navigate to root URL (`/`) | Redirects to `/login` page |
| 2 | Click "Sign in with Google" | Redirects to Google OAuth consent screen |
| 3 | Complete Google sign-in | Redirects back to app, then to `/dashboard` |
| 4 | Check Local Storage | `auth_token` and `refresh_token` exist |
| 5 | Refresh the page | User remains logged in (no redirect to login) |
| 6 | Click "Logout" (if available) or clear tokens | Redirects to `/login` |

**Troubleshooting**:
*   *Issue*: "Sign in with Google" button does nothing.
    *   *Fix*: Check console for errors. Verify `VITE_API_BASE_URL` is set correctly.
*   *Issue*: Redirect loop or 401 errors.
    *   *Fix*: Clear Local Storage manually (`Application` tab -> `Local Storage`) and retry.

### 2. Trip Management

**Goal**: Verify users can create, view, and manage trips with AI integration.

| Step | Action | Expected Outcome |
| :--- | :--- | :--- |
| 1 | Click "Create New Trip" (or "+") | Navigates to Trip Wizard |
| 2 | Enter destination (e.g., "Paris") |  |
| 3 | Select dates (e.g., next week) |  |
| 4 | Add travelers (e.g., Mom, Dad, Child) |  |
| 5 | Submit form | "Generating packing list..." loading state appears |
| 6 | Wait for completion (~15-25s for comprehensive AI generation) | Redirects to Dashboard with new trip selected |
| 7 | Verify Dashboard | Trip details (dates, weather) and comprehensive packing lists appear |
| 8 | Check Packing Lists | Verify comprehensive items across 9 categories (clothing, toiletries, health, documents, electronics, comfort, activities, baby, misc) |
| 9 | Verify Age-Appropriate Items | Child travelers should have age-appropriate items (kid-friendly toiletries, comfort items, entertainment) |
| 10 | Check Weather Adaptations | Items should match weather conditions (rain gear for rainy weather, layers for variable conditions) |
| 11 | Verify Activity Gear | Activity-specific items should appear in 'activities' category (hiking boots, ski gear, beach items) |
| 12 | Check Quantities | Clothing quantities should be realistic based on trip duration and laundry access |
| 13 | Verify Essential Items | Critical items (passports, medications, chargers) should be marked as essential |

**Troubleshooting**:
*   *Issue*: Infinite loading on trip creation.
    *   *Fix*: Check backend terminal for errors. Ensure LLM service is configured/mocked.
*   *Issue*: "Failed to create trip" toast.
    *   *Fix*: Check Network tab response for specific error details.

### 3. Packing List Operations

**Goal**: Verify granular control over packing items (Phase 3).

| Step | Action | Expected Outcome |
| :--- | :--- | :--- |
| 1 | **Toggle Item**: Click a checkbox | Checkbox updates immediately (optimistic UI). Network request to `/toggle-packed` succeeds (200 OK). |
| 2 | **Add Item**: Click "+ Add Item" | Dialog opens. Enter name/category. Item appears in list. Network request to `/items` succeeds. |
| 3 | **Edit Item**: Click edit icon (pencil) | Dialog opens. Change name/quantity. Item updates in list. Network request to `/items/{id}` succeeds. |
| 4 | **Delete Item**: Click delete icon (trash) | Item disappears from list. Network request to `/items/{id}` succeeds. |
| 5 | **Change Category**: Drag item to new category | Item moves to new category. Network request updates category. |
| 6 | **Delegate**: Select "Delegate" option | Dialog opens. Select new owner. Item moves to that person's list. |

**Troubleshooting**:
*   *Issue*: Checkbox toggles then reverts back.
    *   *Fix*: API call failed. Check Network tab. Ensure you have internet connection if backend calls external services.

### 4. Collaboration & Nudges

**Goal**: Verify social features work correctly.

| Step | Action | Expected Outcome |
| :--- | :--- | :--- |
| 1 | Open "Nudge" dialog | List of travelers appears. |
| 2 | Send nudge to a traveler | Success toast appears. Email sent (simulated in logs). |
| 3 | Check "Share" feature | Clicking share generates a link. |

## Debugging Tips

**Useful Console Commands**:

```javascript
// Check current auth state
localStorage.getItem('auth_token')

// Check API configuration
console.log(import.meta.env.VITE_API_BASE_URL)

// Force logout
localStorage.clear(); window.location.reload()
```

**Network Monitoring**:
*   Filter Network tab by `Fetch/XHR`.
*   Look for requests to `localhost:8000`.
*   Red text indicates failed requests - click to see response payload.