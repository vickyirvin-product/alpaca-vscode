

# Kid Mode Quantity & Underwear Icon Improvements

## Overview
Redesign Kid Mode packing item cards to feature prominently sized quantity digits with a checkbox, and fix the underwear item icon.

---

## 1. Kid Mode Card Redesign - Big Quantity with Checkbox

### Current State
- Quantity is shown as a small `×{item.quantity}` badge at the bottom of the card
- Checkbox is only shown as a checkmark overlay when item is packed
- Font size is `text-xs`

### New Design
Transform the card layout to prominently feature:
- **Large checkbox** on the left side of the card (visible before packing)
- **Very large quantity digit** next to or near the checkbox
- Quantity digits sized at `text-4xl` to `text-6xl` (scaling with kid level)

### Visual Layout (per card)
```text
+----------------------------------+
|  [ ]  7       👕                 |
|       ^^      T-Shirts           |
|    checkbox   big qty            |
|    + digit                       |
+----------------------------------+
```

Alternative stacked layout (better for square cards):
```text
+------------------+
|        👕        |
|     T-Shirts     |
|  [✓]    ×7       |
|   ^      ^       |
|  big    huge     |
|  check  digit    |
+------------------+
```

### Implementation
**File**: `src/components/packing/KidModePackingView.tsx`

Changes to the item card (lines 255-311):
1. Add a prominent checkbox component that's always visible
2. Move quantity display to be next to the checkbox at the bottom
3. Scale quantity text to `text-3xl` / `text-4xl` / `text-5xl` based on kid level
4. Style the checkbox to be large and kid-friendly
5. Remove the small `×` prefix, just show the number prominently

---

## 2. Underwear Icon Fix

### Current State
Both Emma's and Lucas's "Underwear" items use `👙` (bikini/bathing suit emoji)

### Fix
Change to `🩲` (briefs emoji) which represents actual underwear

**File**: `src/data/mockData.ts`

Changes:
- Line 103: Change Emma's underwear from `'👙'` to `'🩲'`
- Line 118: Change Lucas's underwear from `'👙'` to `'🩲'`

---

## Technical Details

### Kid Mode Level Scaling for Quantity
Update `getLevelStyles()` to include quantity sizing:

```typescript
const getLevelStyles = () => {
  switch (kidModeLevel) {
    case 'little':
      return {
        cardSize: 'text-5xl md:text-6xl',
        gridCols: 'grid-cols-2 sm:grid-cols-2 md:grid-cols-3',
        fontSize: 'text-base md:text-lg',
        quantitySize: 'text-4xl md:text-5xl',  // NEW
        checkboxSize: 'w-8 h-8',               // NEW
      };
    case 'teenager':
      return {
        cardSize: 'text-3xl md:text-4xl',
        gridCols: 'grid-cols-3 sm:grid-cols-4 md:grid-cols-5',
        fontSize: 'text-xs md:text-sm',
        quantitySize: 'text-2xl md:text-3xl',  // NEW
        checkboxSize: 'w-5 h-5',               // NEW
      };
    default: // big
      return {
        cardSize: 'text-4xl md:text-5xl',
        gridCols: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4',
        fontSize: 'text-sm md:text-base',
        quantitySize: 'text-3xl md:text-4xl',  // NEW
        checkboxSize: 'w-6 h-6',               // NEW
      };
  }
};
```

### Card Layout Changes
Replace the current quantity badge section with:

```tsx
{/* Bottom row: Checkbox + Quantity */}
<div className="flex items-center justify-center gap-3 mt-2">
  {/* Large Checkbox */}
  <div className={cn(
    "rounded-lg border-3 flex items-center justify-center transition-all",
    levelStyles.checkboxSize,
    item.isPacked 
      ? "bg-success border-success" 
      : "bg-white border-vault"
  )}>
    {item.isPacked && <Check className="text-white w-5 h-5" />}
  </div>
  
  {/* Large Quantity */}
  {item.quantity > 1 && (
    <span className={cn(
      "font-black",
      levelStyles.quantitySize,
      item.isPacked ? "text-white" : "text-primary"
    )}>
      {item.quantity}
    </span>
  )}
</div>
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/components/packing/KidModePackingView.tsx` | Redesign card layout with large checkbox + quantity |
| `src/data/mockData.ts` | Change underwear emoji from 👙 to 🩲 |

