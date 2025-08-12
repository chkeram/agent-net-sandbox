# Project Setup: Creating a Modern React Application

## Overview

In this chapter, we'll set up a React application from scratch using **Vite**, the modern build tool that's replacing Create React App. You'll understand every file and configuration.

## Why These Tools?

### Vite vs Create React App (CRA)
- **Vite**: Lightning fast, uses native ES modules, instant hot reload
- **CRA**: Slower, uses Webpack, being phased out by React team

### TypeScript vs JavaScript
- **TypeScript**: Catches errors before runtime, better autocomplete
- **JavaScript**: No compilation step, but more runtime errors

## Step 1: Initialize the Project

### Creating the Frontend Directory

```bash
# From the project root
mkdir frontend
cd frontend
```

### Initialize with Vite

```bash
npm create vite@latest . -- --template react-ts
```

**What this does:**
- `npm create vite@latest` - Uses the latest Vite version
- `.` - Create in current directory
- `--template react-ts` - Use React with TypeScript template

### Install Dependencies

```bash
npm install
```

This reads `package.json` and installs all required packages into `node_modules/`.

## Step 2: Understanding the Generated Files

### package.json
```json
{
  "name": "frontend",
  "version": "0.0.0",
  "scripts": {
    "dev": "vite",           // Start development server
    "build": "vite build",   // Build for production
    "preview": "vite preview" // Preview production build
  },
  "dependencies": {
    "react": "^18.3.1",      // React library
    "react-dom": "^18.3.1"   // React DOM renderer
  },
  "devDependencies": {
    "@types/react": "^18.3.0", // TypeScript types for React
    "vite": "^5.0.0",          // Build tool
    "typescript": "^5.0.0"     // TypeScript compiler
  }
}
```

### Key Files Explained

#### index.html (Entry Point)
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React + TS</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- Vite injects the script automatically -->
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Key Points:**
- `<div id="root">` - Where React renders the app
- `type="module"` - Uses ES6 modules (modern JavaScript)

#### src/main.tsx (JavaScript Entry)
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**What's happening:**
1. Import React and our App component
2. Find the `root` div in HTML
3. Render our App inside it
4. `StrictMode` helps find potential problems

#### src/App.tsx (Main Component)
```tsx
function App() {
  return (
    <div>
      <h1>Hello World</h1>
    </div>
  )
}

export default App
```

## Step 3: Adding Our Dependencies

### Core Dependencies

```bash
# UI Libraries
npm install react-markdown remark-gfm react-syntax-highlighter
npm install clsx tailwind-merge lucide-react uuid

# Type Definitions (for TypeScript)
npm install -D @types/react-syntax-highlighter @types/uuid
```

**What each does:**
- `react-markdown` - Render markdown in React
- `remark-gfm` - GitHub Flavored Markdown support
- `react-syntax-highlighter` - Syntax highlighting for code blocks
- `clsx` - Utility for conditional CSS classes
- `tailwind-merge` - Merge Tailwind classes safely
- `lucide-react` - Beautiful icon library
- `uuid` - Generate unique IDs

### Tailwind CSS Setup

```bash
# Install Tailwind and its dependencies
npm install -D tailwindcss @tailwindcss/postcss autoprefixer
```

## Step 4: Configuration Files

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Watch all source files
  ],
  theme: {
    extend: {}, // Custom theme extensions go here
  },
  plugins: [],
}
```

### postcss.config.js
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {}, // Process Tailwind CSS
  },
}
```

### src/index.css
```css
@import "tailwindcss"; /* Import all Tailwind styles */

:root {
  /* CSS Variables for theming */
  font-family: Inter, system-ui, Arial, sans-serif;
  line-height: 1.5;
  
  /* Dark mode by default */
  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;
}

/* Light mode when system prefers it */
@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
}
```

## Step 5: TypeScript Configuration

### tsconfig.json (Root Config)
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

### tsconfig.app.json (App Config)
```json
{
  "compilerOptions": {
    "target": "ES2022",           // Modern JavaScript features
    "lib": ["ES2022", "DOM"],     // Available APIs
    "module": "ESNext",           // Module system
    "jsx": "react-jsx",           // JSX handling
    "strict": true,               // Strict type checking
    "moduleResolution": "bundler", // How to find modules
    "allowImportingTsExtensions": true, // Allow .ts imports
    "noEmit": true                // Vite handles compilation
  },
  "include": ["src"]              // What to compile
}
```

**Important Settings:**
- `strict: true` - Enables all strict type checking
- `jsx: "react-jsx"` - New JSX transform (no need to import React)
- `allowImportingTsExtensions` - Requires `.ts` in imports

## Step 6: Development Workflow

### Starting the Dev Server

```bash
npm run dev
```

This starts Vite's dev server with:
- **Hot Module Replacement (HMR)** - Instant updates without refresh
- **Fast Refresh** - Preserves component state during edits
- **Error Overlay** - Shows errors in the browser

### Building for Production

```bash
npm run build
```

Creates optimized files in `dist/`:
- Minified JavaScript
- Optimized CSS
- Code splitting
- Tree shaking (removes unused code)

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

## Common Issues and Solutions

### Issue: "Cannot find module" Errors
```typescript
// ❌ Without extension (might fail)
import { Message } from './types/chat'

// ✅ With extension (required by our config)
import { Message } from './types/chat.ts'
```

### Issue: Tailwind Classes Not Working
```css
/* ❌ Old Tailwind syntax */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ✅ Tailwind v4 syntax */
@import "tailwindcss";
```

### Issue: TypeScript Import Errors
```typescript
// ❌ Importing types as values
import { Message } from './types/chat.ts'

// ✅ Type-only import
import type { Message } from './types/chat.ts'
```

## File Structure Best Practices

### Organizing Components
```
src/
├── components/
│   ├── Chat/           # Feature folder
│   │   ├── ChatContainer.tsx
│   │   ├── ChatInput.tsx
│   │   └── Message.tsx
│   └── Layout/         # Layout components
│       ├── Header.tsx
│       └── Sidebar.tsx
├── types/              # TypeScript types
│   ├── chat.ts
│   └── agent.ts
├── hooks/              # Custom React hooks
├── utils/              # Helper functions
└── services/           # API calls
```

### Naming Conventions
- **Components**: PascalCase (`ChatInput.tsx`)
- **Utilities**: camelCase (`formatDate.ts`)
- **Types**: PascalCase (`Message`, `Agent`)
- **Files**: Match export name (`ChatInput.tsx` exports `ChatInput`)

## Environment Variables

### Creating .env.local
```bash
# For local development secrets
VITE_API_URL=http://localhost:8004
VITE_ENABLE_DEBUG=true
```

### Accessing in Code
```typescript
const apiUrl = import.meta.env.VITE_API_URL
// Only variables prefixed with VITE_ are exposed
```

## VS Code Setup (Recommended)

### Extensions to Install
1. **ESLint** - Linting
2. **Prettier** - Code formatting
3. **Tailwind CSS IntelliSense** - Tailwind autocomplete
4. **TypeScript Vue Plugin** - Better TS support

### Settings (`.vscode/settings.json`)
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "\"([^\"]*)\""]
  ]
}
```

## Understanding the Build Process

### Development Flow
```
index.html → main.tsx → App.tsx → Components
     ↓          ↓          ↓           ↓
  Browser    React      Your App    UI Render
```

### Build Process
```
Source Files → TypeScript → Vite → Bundle → dist/
     ↓            ↓          ↓        ↓        ↓
   .tsx/.ts     Check      Build   Optimize  Deploy
```

## Next Steps

Now that your environment is set up, you're ready to learn about React components. Head to [03-understanding-components.md](./03-understanding-components.md) to understand how React components work.

## Quick Reference

### Commands
```bash
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
npm install pkg  # Add a dependency
npm install -D pkg # Add a dev dependency
```

### File Extensions
- `.tsx` - TypeScript with JSX (React components)
- `.ts` - Pure TypeScript (utilities, types)
- `.css` - Stylesheets
- `.json` - Configuration files

### Port Numbers
- `5173` - Vite dev server default port
- `4173` - Vite preview server default port
- `8004` - Our orchestrator API (backend)

---

**Previous**: [01-introduction.md](./01-introduction.md) | **Next**: [03-understanding-components.md](./03-understanding-components.md)