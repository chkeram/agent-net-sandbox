# Troubleshooting Guide

## Common Issues and Solutions

This guide covers the most common issues you'll encounter while developing the chat interface and how to fix them.

---

## 🔴 Build & Compilation Errors

### Issue: "Cannot find module" Error
```
Cannot find module './types/chat' or its corresponding type declarations
```

**Cause**: TypeScript can't find the import path.

**Solutions:**
```typescript
// ❌ Wrong: Missing extension
import { Message } from './types/chat'

// ✅ Correct: With .ts extension (required by our tsconfig)
import { Message } from './types/chat.ts'

// ✅ For type-only imports
import type { Message } from './types/chat.ts'
```

### Issue: "The requested module does not provide an export"
```
Uncaught SyntaxError: The requested module '/src/types/chat.ts' 
does not provide an export named 'Message'
```

**Cause**: Import/export mismatch or using value import for types.

**Solutions:**
```typescript
// Check the export in chat.ts
export interface Message { ... }  // ✅ Named export

// Use type import for interfaces
import type { Message } from './types/chat.ts'  // ✅ Type import
```

### Issue: PostCSS/Tailwind Error
```
[postcss] It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin
```

**Cause**: Tailwind v4 requires different PostCSS setup.

**Solution 1**: Update PostCSS config
```javascript
// postcss.config.js
export default {
  plugins: {
    '@tailwindcss/postcss': {},  // For Tailwind v4
  },
}
```

**Solution 2**: Use correct import in CSS
```css
/* For Tailwind v4 */
@import "tailwindcss";

/* Not the old v3 syntax: */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## 🎨 Styling Issues

### Issue: Tailwind Classes Not Working
Page appears unstyled, classes have no effect.

**Checklist:**
1. **PostCSS configured?**
   ```bash
   # Check if postcss.config.js exists
   ls postcss.config.js
   ```

2. **Tailwind imported in CSS?**
   ```css
   /* src/index.css */
   @import "tailwindcss";
   ```

3. **Content paths configured?**
   ```javascript
   // tailwind.config.js
   content: [
     "./index.html",
     "./src/**/*.{js,ts,jsx,tsx}",
   ]
   ```

4. **Dev server restarted?**
   ```bash
   # Restart Vite
   npm run dev
   ```

### Issue: Dark Mode Not Working
Dark mode classes have no effect.

**Solutions:**
1. **Check system preferences**
   - macOS: System Preferences → Appearance
   - Windows: Settings → Personalization → Colors

2. **Ensure dark variants exist**
   ```jsx
   // Need both light and dark classes
   className="bg-white dark:bg-gray-800"
   ```

3. **Check CSS variables**
   ```css
   /* index.css should have */
   @media (prefers-color-scheme: dark) {
     :root {
       /* dark mode colors */
     }
   }
   ```

### Issue: Layout Breaking on Mobile
Content overflows or looks wrong on small screens.

**Solutions:**
```jsx
// Add responsive classes
<div className="w-full md:w-3/4 lg:w-1/2">

// Prevent overflow
<div className="overflow-x-auto">

// Mobile-specific padding
<div className="p-2 md:p-4 lg:p-8">
```

---

## ⚛️ React Issues

### Issue: "Too many re-renders"
```
Error: Too many re-renders. React limits the number 
of renders to prevent an infinite loop.
```

**Cause**: State update in render or incorrect event handler.

**Wrong:**
```jsx
// ❌ Calls function immediately
<button onClick={handleClick()}>

// ❌ Updates state during render
function Component() {
  const [count, setCount] = useState(0);
  setCount(count + 1);  // Infinite loop!
}
```

**Correct:**
```jsx
// ✅ Pass function reference
<button onClick={handleClick}>

// ✅ Update state in event/effect
function Component() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    setCount(count + 1);
  }, []);  // Runs once
}
```

### Issue: State Not Updating
Click button but nothing happens.

**Common Causes:**

1. **Direct mutation:**
   ```jsx
   // ❌ Mutating state
   const [items, setItems] = useState([1, 2]);
   items.push(3);  // Won't trigger re-render
   
   // ✅ Create new array
   setItems([...items, 3]);
   ```

2. **Stale closure:**
   ```jsx
   // ❌ Uses old state value
   setTimeout(() => {
     setCount(count + 1);
   }, 1000);
   
   // ✅ Use function form
   setTimeout(() => {
     setCount(prev => prev + 1);
   }, 1000);
   ```

### Issue: useEffect Running Infinitely
Effect keeps triggering repeatedly.

**Cause**: Missing or incorrect dependencies.

```jsx
// ❌ Missing dependency
useEffect(() => {
  fetchData(userId);
}, []);  // userId change won't trigger

// ❌ Object/array dependency
useEffect(() => {
  // Runs every render because {} !== {}
}, [{}]);

// ✅ Correct dependencies
useEffect(() => {
  fetchData(userId);
}, [userId]);

// ✅ Stable reference
const config = useMemo(() => ({ key: 'value' }), []);
useEffect(() => {
  // Only runs when config actually changes
}, [config]);
```

---

## 📝 TypeScript Errors

### Issue: "Property does not exist on type"
```
Property 'name' does not exist on type 'never'
```

**Solutions:**

1. **Define interface:**
   ```typescript
   interface User {
     name: string;
     age: number;
   }
   
   const user: User = { name: 'John', age: 30 };
   ```

2. **Type assertions:**
   ```typescript
   const data = JSON.parse(response) as User;
   ```

3. **Type guards:**
   ```typescript
   if ('name' in user) {
     console.log(user.name);
   }
   ```

### Issue: "Type 'string | undefined' is not assignable"
Optional props causing type errors.

**Solutions:**
```typescript
// Use optional chaining
const name = user?.name ?? 'Default';

// Type narrowing
if (user?.name) {
  // name is string here, not undefined
  console.log(user.name.toUpperCase());
}

// Default parameters
function greet(name: string = 'Guest') {
  return `Hello ${name}`;
}
```

---

## 🌐 API & Network Issues

### Issue: CORS Error
```
Access to fetch at 'http://localhost:8004' from origin 
'http://localhost:5173' has been blocked by CORS policy
```

**Solutions:**

1. **Check orchestrator CORS config:**
   ```python
   # In orchestrator API
   app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],  # Or specific origins
     allow_methods=["*"],
     allow_headers=["*"],
   )
   ```

2. **Proxy through Vite:**
   ```javascript
   // vite.config.ts
   export default {
     server: {
       proxy: {
         '/api': 'http://localhost:8004'
       }
     }
   }
   ```

### Issue: "Failed to fetch" or Network Error
Can't connect to backend API.

**Checklist:**
1. **Is orchestrator running?**
   ```bash
   docker-compose ps
   # Should show orchestrator as "Up"
   ```

2. **Correct port?**
   ```javascript
   // Should be 8004 for orchestrator
   fetch('http://localhost:8004/process')
   ```

3. **Health check:**
   ```bash
   curl http://localhost:8004/health
   ```

---

## 🐳 Docker Issues

### Issue: "Port already in use"
```
Error: Port 5173 is already in use
```

**Solutions:**
```bash
# Find what's using the port
lsof -i :5173  # macOS/Linux
netstat -ano | findstr :5173  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux

# Or use different port
npm run dev -- --port 3000
```

### Issue: Docker Services Not Starting
```
ERROR: for orchestrator Cannot start service
```

**Solutions:**
```bash
# Clean restart
docker-compose down
docker-compose up -d

# Rebuild if needed
docker-compose build --no-cache orchestrator
docker-compose up -d

# Check logs
docker-compose logs orchestrator
```

---

## 💾 Local Storage Issues

### Issue: Messages Not Persisting
Messages disappear on refresh.

**Debug Steps:**
1. **Check browser console:**
   ```javascript
   // See what's stored
   console.log(localStorage.getItem('chat-messages'))
   ```

2. **Check parsing:**
   ```javascript
   try {
     const messages = JSON.parse(localStorage.getItem('chat-messages'));
     console.log(messages);
   } catch (e) {
     console.error('Parse error:', e);
   }
   ```

3. **Clear corrupted data:**
   ```javascript
   localStorage.removeItem('chat-messages');
   // Or clear everything
   localStorage.clear();
   ```

---

## 🔧 Development Environment

### Issue: "command not found: npm"
Node.js not installed or not in PATH.

**Solution:**
```bash
# Install Node.js
# macOS with Homebrew
brew install node

# Or download from nodejs.org
# Verify installation
node --version  # Should be v18+
npm --version
```

### Issue: Module Not Found After Install
Installed package but still getting errors.

**Solutions:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Restart dev server
npm run dev
```

### Issue: Hot Reload Not Working
Changes not reflected in browser.

**Solutions:**
1. **Check file watching:**
   ```javascript
   // vite.config.ts
   export default {
     server: {
       watch: {
         usePolling: true,  // For Docker/WSL
       }
     }
   }
   ```

2. **Clear Vite cache:**
   ```bash
   rm -rf node_modules/.vite
   npm run dev
   ```

---

## 🎯 Quick Fixes Checklist

When something's not working, try these in order:

1. **Refresh the browser** (Cmd/Ctrl + R)
2. **Hard refresh** (Cmd/Ctrl + Shift + R)
3. **Restart dev server** (Ctrl + C, then `npm run dev`)
4. **Clear node_modules:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```
5. **Check browser console** for errors
6. **Check terminal** for build errors
7. **Verify all services running:**
   ```bash
   docker-compose ps
   ```

---

## 📚 Debugging Tools

### Browser DevTools
- **Console**: Check for JavaScript errors
- **Network**: Monitor API calls
- **Elements**: Inspect DOM and styles
- **React DevTools**: Install extension for component debugging

### VS Code Extensions
- **Error Lens**: Shows errors inline
- **Console Ninja**: Shows console.log in editor
- **Thunder Client**: Test API endpoints

### Useful Commands
```bash
# Check what's running
ps aux | grep node
docker ps
lsof -i :5173

# Monitor logs
docker-compose logs -f orchestrator
tail -f npm-debug.log

# Network debugging
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

---

## 🆘 Getting More Help

### 1. Error Messages
Always read the full error message. The solution is often in the details.

### 2. Documentation
- React: https://react.dev
- TypeScript: https://www.typescriptlang.org/docs
- Tailwind: https://tailwindcss.com/docs
- Vite: https://vitejs.dev/guide

### 3. Search Strategy
```
"[ERROR MESSAGE]" site:stackoverflow.com
"[ERROR MESSAGE]" React TypeScript
Vite "[ERROR MESSAGE]"
```

### 4. Debug Strategy
1. Isolate the problem (comment out code)
2. Check simplest case first
3. Add console.log to trace execution
4. Use debugger statement
5. Check network tab for API issues

---

**Remember**: Most errors have been encountered before. Stay calm, read the error carefully, and work through the solutions systematically.

---

**Back to**: [README.md](./README.md) | **Start Tutorial**: [01-introduction.md](./01-introduction.md)