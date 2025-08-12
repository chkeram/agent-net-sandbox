# Styling with Tailwind CSS

## What is Tailwind CSS?

Tailwind is a **utility-first CSS framework**. Instead of writing custom CSS, you apply pre-built classes directly in your HTML/JSX.

### Traditional CSS vs Tailwind

**Traditional CSS:**
```css
/* styles.css */
.message-container {
  display: flex;
  padding: 1rem;
  background-color: white;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
}
```
```jsx
<div className="message-container">
```

**Tailwind CSS:**
```jsx
<div className="flex p-4 bg-white rounded-lg mb-2">
```

No separate CSS file needed! 🎉

## Core Concepts

### 1. Utility Classes

Each class does one thing:
- `p-4` = padding: 1rem
- `bg-white` = background-color: white
- `flex` = display: flex
- `rounded-lg` = border-radius: 0.5rem

### 2. Responsive Design

Add breakpoint prefixes for responsive designs:
```jsx
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on tablet, third on desktop */}
</div>
```

Breakpoints:
- `sm:` ≥640px
- `md:` ≥768px  
- `lg:` ≥1024px
- `xl:` ≥1280px
- `2xl:` ≥1536px

### 3. Dark Mode

Tailwind supports dark mode with the `dark:` prefix:
```jsx
<div className="bg-white dark:bg-gray-800 text-black dark:text-white">
  {/* White background in light mode, dark gray in dark mode */}
</div>
```

## Common Tailwind Classes

### Spacing
```jsx
// Padding
p-0   // 0
p-1   // 0.25rem
p-2   // 0.5rem
p-4   // 1rem
p-8   // 2rem

// Specific sides
pt-4  // padding-top
pr-4  // padding-right
pb-4  // padding-bottom
pl-4  // padding-left
px-4  // padding left & right
py-4  // padding top & bottom

// Margin (same scale as padding)
m-4   // margin: 1rem
mx-auto // margin-left: auto; margin-right: auto
```

### Flexbox
```jsx
// Container
flex           // display: flex
flex-row       // flex-direction: row (default)
flex-col       // flex-direction: column
justify-center // justify-content: center
items-center   // align-items: center
gap-4         // gap: 1rem

// Children
flex-1        // flex: 1 1 0%
flex-shrink-0 // flex-shrink: 0
```

### Colors
```jsx
// Text colors
text-white
text-black
text-gray-500  // Medium gray
text-blue-600  // Blue

// Background colors
bg-white
bg-gray-100    // Light gray
bg-blue-500    // Blue

// Border colors
border-gray-300
```

### Typography
```jsx
// Font size
text-xs   // 0.75rem
text-sm   // 0.875rem
text-base // 1rem
text-lg   // 1.125rem
text-xl   // 1.25rem
text-2xl  // 1.5rem

// Font weight
font-normal   // 400
font-medium   // 500
font-semibold // 600
font-bold     // 700

// Text alignment
text-left
text-center
text-right
```

### Layout
```jsx
// Width
w-full    // width: 100%
w-1/2     // width: 50%
w-64      // width: 16rem
max-w-4xl // max-width: 56rem

// Height
h-full    // height: 100%
h-screen  // height: 100vh
h-64      // height: 16rem
```

## Our Chat UI Styles Explained

Let's break down the actual Tailwind classes we use:

### Message Component
```jsx
<div className={clsx(
  'flex gap-3 p-4',
  isUser ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900'
)}>
```

**Breaking it down:**
- `flex` - Display as flexbox
- `gap-3` - 0.75rem gap between children
- `p-4` - 1rem padding all around
- `bg-white` - White background
- `dark:bg-gray-800` - Dark gray in dark mode
- Conditional classes based on `isUser`

### Avatar Styling
```jsx
<div className={clsx(
  'w-8 h-8 rounded-full flex items-center justify-center',
  isUser ? 'bg-blue-500' : 'bg-green-500'
)}>
```

**What each does:**
- `w-8 h-8` - 2rem × 2rem square
- `rounded-full` - Perfect circle
- `flex items-center justify-center` - Center the icon
- `bg-blue-500` - Blue background for user
- `bg-green-500` - Green for assistant

### Chat Input
```jsx
<textarea
  className={clsx(
    "flex-1 resize-none rounded-lg border",
    "px-4 py-2 text-sm focus:outline-none focus:ring-2",
    "dark:border-gray-700 dark:bg-gray-900 dark:text-white",
    isLoading ? "opacity-50 cursor-not-allowed" : "focus:ring-blue-500"
  )}
/>
```

**Key patterns:**
- Multiple class strings for organization
- `focus:` prefix for focus states
- `dark:` prefix for dark mode
- Conditional opacity when loading

## Using clsx for Dynamic Classes

The `clsx` utility helps combine classes conditionally:

```jsx
import { clsx } from 'clsx';

// Basic usage
clsx('base-class', 'another-class')
// Result: "base-class another-class"

// Conditional classes
clsx('base', {
  'active': isActive,
  'disabled': isDisabled
})

// With arrays
clsx(['base', isLarge && 'text-lg'])

// Our real example
const buttonClass = clsx(
  'px-4 py-2 rounded', // Always applied
  {
    'bg-blue-500 text-white': variant === 'primary',
    'bg-gray-200 text-black': variant === 'secondary',
    'opacity-50 cursor-not-allowed': disabled
  }
);
```

## Dark Mode Implementation

### System Preference Detection

Our CSS follows system preferences:
```css
/* index.css */
@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
}
```

### Dark Mode Classes
```jsx
// Component automatically adapts
<div className="bg-white dark:bg-gray-900">
  <h1 className="text-black dark:text-white">
    Adapts to theme
  </h1>
</div>
```

## Responsive Design Patterns

### Mobile-First Approach
```jsx
<div className="
  w-full        // Mobile: full width
  md:w-3/4      // Tablet: 75% width
  lg:w-1/2      // Desktop: 50% width
  xl:max-w-4xl  // Large screens: max width
">
```

### Hide/Show Elements
```jsx
// Hide on mobile, show on desktop
<div className="hidden lg:block">
  Desktop only
</div>

// Show on mobile, hide on desktop
<div className="block lg:hidden">
  Mobile only
</div>
```

## Custom Styles When Needed

Sometimes you need custom CSS. Add it to `index.css`:

```css
/* index.css */
@import "tailwindcss";

/* Custom scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}
```

Then use it:
```jsx
<div className="custom-scrollbar overflow-y-auto">
```

## Animation Classes

Tailwind includes animation utilities:

```jsx
// Pulse animation (for loading)
<div className="animate-pulse">Loading...</div>

// Spin (for spinners)
<div className="animate-spin">⟳</div>

// Bounce (for attention)
<div className="animate-bounce">↓</div>

// Our loading dots
<div className="animate-bounce" style={{ animationDelay: '0ms' }} />
<div className="animate-bounce" style={{ animationDelay: '150ms' }} />
<div className="animate-bounce" style={{ animationDelay: '300ms' }} />
```

## Layout Patterns

### Centered Container
```jsx
<div className="max-w-4xl mx-auto">
  {/* Content centered with max width */}
</div>
```

### Full Height Layout
```jsx
<div className="h-screen flex flex-col">
  <header className="h-16">Header</header>
  <main className="flex-1 overflow-y-auto">Content</main>
  <footer className="h-20">Footer</footer>
</div>
```

### Sidebar Layout
```jsx
<div className="flex h-screen">
  <aside className="w-64 bg-gray-100">Sidebar</aside>
  <main className="flex-1">Main content</main>
</div>
```

## Our Chat Layout Structure

Here's how our chat UI is structured with Tailwind:

```jsx
// App.tsx - Full screen container
<div className="h-screen bg-gray-100 dark:bg-gray-900">

  // ChatContainer - Flex column layout
  <div className="flex flex-col h-full">
    
    // Header - Fixed height
    <div className="border-b p-4">
      <div className="max-w-4xl mx-auto">
        {/* Centered content */}
      </div>
    </div>
    
    // MessageList - Flexible height with scroll
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {/* Messages */}
      </div>
    </div>
    
    // ChatInput - Fixed at bottom
    <div className="border-t p-4">
      <div className="max-w-4xl mx-auto">
        {/* Input field */}
      </div>
    </div>
    
  </div>
</div>
```

## Tailwind Best Practices

### 1. Consistent Spacing
Use Tailwind's spacing scale consistently:
```jsx
// ✅ Good: Using scale
p-2, p-4, p-8

// ❌ Bad: Random values
p-[13px], p-[27px]
```

### 2. Group Related Classes
```jsx
// ✅ Organized
className={clsx(
  // Layout
  'flex flex-col gap-4',
  // Spacing
  'p-4 mx-auto',
  // Styling
  'bg-white rounded-lg shadow',
  // Dark mode
  'dark:bg-gray-800'
)}
```

### 3. Extract Complex Combinations
```jsx
// For repeated patterns, create a constant
const cardStyles = 'p-4 bg-white rounded-lg shadow dark:bg-gray-800';

// Use it multiple places
<div className={cardStyles}>
<article className={cardStyles}>
```

### 4. Avoid Arbitrary Values
```jsx
// ❌ Arbitrary values
<div className="w-[523px] p-[17px]">

// ✅ Use scale or semantic values
<div className="w-full max-w-2xl p-4">
```

## Debugging Tailwind

### 1. Classes Not Working?
- Check if class exists in Tailwind
- Ensure PostCSS is configured
- Verify content paths in config

### 2. Dark Mode Not Working?
- Check system preferences
- Add `dark:` prefix to all color classes
- Ensure dark mode is enabled in config

### 3. Responsive Classes Not Working?
- Check viewport width
- Use correct breakpoint prefix
- Remember mobile-first approach

### 4. Dev Tools
```jsx
// Add border to debug layout
<div className="border border-red-500">
  Debug me
</div>

// Add background to see element bounds
<div className="bg-red-100">
  Visible bounds
</div>
```

## Performance Tips

### 1. Use PurgeCSS (Built into Tailwind)
Tailwind automatically removes unused styles in production.

### 2. Avoid Dynamic Class Names
```jsx
// ❌ Won't be included in build
const color = 'blue';
<div className={`bg-${color}-500`}>

// ✅ Will be included
<div className={isBlue ? 'bg-blue-500' : 'bg-red-500'}>
```

### 3. Group Hover States
```jsx
// Add group to parent
<div className="group hover:bg-gray-100">
  <h3>Title</h3>
  // Child responds to parent hover
  <p className="group-hover:text-blue-500">
    Turns blue on parent hover
  </p>
</div>
```

## Summary

Tailwind CSS provides:
- Rapid development with utility classes
- Consistent design system
- Built-in responsive design
- Dark mode support
- No context switching between files

Key takeaways:
1. Each class does one thing
2. Combine classes for complex styles
3. Use prefixes for states (hover:, focus:, dark:)
4. Mobile-first responsive design
5. Keep classes organized and readable

---

**Previous**: [03-understanding-components.md](./03-understanding-components.md) | **Next**: [05-typescript-basics.md](./05-typescript-basics.md)