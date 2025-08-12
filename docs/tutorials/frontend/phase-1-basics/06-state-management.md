# State Management in React

## What is State?

State is **data that changes over time** in your application. When state changes, React re-renders the component to reflect the new data.

### Props vs State

| Props | State |
|-------|-------|
| Passed from parent | Owned by component |
| Read-only | Can be changed |
| External data | Internal data |
| Like function parameters | Like function variables |

## The useState Hook

`useState` is how you add state to functional components:

```typescript
import { useState } from 'react';

function Counter() {
  // Declare state variable
  const [count, setCount] = useState(0);
  //     ^state  ^setter        ^initial value
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}
```

### useState Syntax

```typescript
const [state, setState] = useState(initialValue);
```

- **state**: Current value
- **setState**: Function to update the value
- **initialValue**: Starting value

### Our Chat Input Example

```typescript
export const ChatInput = () => {
  const [input, setInput] = useState('');
  
  return (
    <textarea
      value={input}                    // Controlled by state
      onChange={(e) => setInput(e.target.value)}  // Update state
    />
  );
};
```

## State with TypeScript

### Basic Types
```typescript
// String state
const [name, setName] = useState<string>('');

// Number state
const [age, setAge] = useState<number>(0);

// Boolean state
const [isVisible, setIsVisible] = useState<boolean>(false);

// Object state
interface User {
  name: string;
  email: string;
}
const [user, setUser] = useState<User | null>(null);

// Array state
const [items, setItems] = useState<string[]>([]);
```

### Our Message State
```typescript
import type { Message } from '../../types/chat.ts';

export const ChatContainer = () => {
  // Array of messages
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Loading state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Error state
  const [error, setError] = useState<string | null>(null);
};
```

## State Update Patterns

### Direct Updates
```typescript
// Simple value update
setCount(5);
setName('Alice');
setIsVisible(true);
```

### Functional Updates
When new state depends on previous state, use a function:

```typescript
// ❌ Problematic with rapid updates
setCount(count + 1);
setCount(count + 1); // Both might use same 'count' value

// ✅ Guaranteed to use latest state
setCount(prev => prev + 1);
setCount(prev => prev + 1); // Each uses updated value
```

### Object State Updates
```typescript
const [user, setUser] = useState({ name: 'Alice', age: 30 });

// ❌ Direct mutation (won't trigger re-render)
user.age = 31;
setUser(user);

// ✅ Create new object
setUser({ ...user, age: 31 });

// ✅ Or with functional update
setUser(prev => ({ ...prev, age: 31 }));
```

### Array State Updates
```typescript
const [items, setItems] = useState(['a', 'b', 'c']);

// ❌ Direct mutation
items.push('d');  // Won't trigger re-render

// ✅ Create new array

// Add item
setItems([...items, 'd']);
setItems(prev => [...prev, 'd']);

// Remove item
setItems(items.filter(item => item !== 'b'));

// Update item
setItems(items.map(item => 
  item === 'b' ? 'updated' : item
));

// Insert at index
const index = 1;
setItems([
  ...items.slice(0, index),
  'new',
  ...items.slice(index)
]);
```

### Our Message Adding Pattern
```typescript
const handleSendMessage = (content: string) => {
  const userMessage: Message = {
    id: uuidv4(),
    role: 'user',
    content,
    timestamp: new Date(),
  };
  
  // Add to messages array
  setMessages(prev => [...prev, userMessage]);
};
```

## The useEffect Hook

`useEffect` handles **side effects** - operations that affect something outside the component:
- API calls
- Timers
- Local storage
- DOM manipulation

### Basic Syntax
```typescript
useEffect(() => {
  // Side effect code
  
  return () => {
    // Cleanup (optional)
  };
}, [dependencies]);
```

### Dependency Array Patterns

```typescript
// Runs after every render
useEffect(() => {
  console.log('Component rendered');
});

// Runs once on mount
useEffect(() => {
  console.log('Component mounted');
}, []);

// Runs when dependencies change
useEffect(() => {
  console.log(`Count changed to ${count}`);
}, [count]);

// Cleanup on unmount
useEffect(() => {
  const timer = setInterval(() => {}, 1000);
  
  return () => {
    clearInterval(timer);  // Cleanup
  };
}, []);
```

### Our Local Storage Example
```typescript
export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Load from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat-messages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed);
      } catch (error) {
        console.error('Failed to load messages:', error);
      }
    }
  }, []); // Empty array = run once
  
  // Save to localStorage when messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]); // Run when messages change
};
```

## Common useEffect Patterns

### API Calls
```typescript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  async function fetchData() {
    try {
      setLoading(true);
      const response = await fetch('/api/data');
      const json = await response.json();
      setData(json);
    } catch (error) {
      console.error('Fetch failed:', error);
    } finally {
      setLoading(false);
    }
  }
  
  fetchData();
}, []); // Fetch once on mount
```

### Subscriptions
```typescript
useEffect(() => {
  const handleResize = () => {
    console.log('Window resized');
  };
  
  window.addEventListener('resize', handleResize);
  
  // Cleanup
  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);
```

### Debouncing
```typescript
const [searchTerm, setSearchTerm] = useState('');
const [results, setResults] = useState([]);

useEffect(() => {
  // Debounce search
  const timer = setTimeout(() => {
    if (searchTerm) {
      searchAPI(searchTerm).then(setResults);
    }
  }, 500);
  
  return () => clearTimeout(timer);
}, [searchTerm]);
```

### Auto-scroll Example
```typescript
const MessageList = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div>
      {messages.map(msg => <Message key={msg.id} {...msg} />)}
      <div ref={bottomRef} />
    </div>
  );
};
```

## Other Important Hooks

### useRef
Holds a mutable value that doesn't trigger re-renders:

```typescript
const inputRef = useRef<HTMLInputElement>(null);

// Focus the input
const focusInput = () => {
  inputRef.current?.focus();
};

return <input ref={inputRef} />;
```

### useCallback
Memoizes a function to prevent recreation:

```typescript
const [count, setCount] = useState(0);

// Without useCallback, new function every render
const increment = () => setCount(count + 1);

// With useCallback, same function unless dependencies change
const increment = useCallback(() => {
  setCount(prev => prev + 1);
}, []); // No dependencies, never recreates
```

### useMemo
Memoizes a computed value:

```typescript
const [items, setItems] = useState([...]);

// Recalculates every render
const expensiveValue = items.reduce((sum, item) => sum + item.value, 0);

// Only recalculates when items change
const expensiveValue = useMemo(() => {
  return items.reduce((sum, item) => sum + item.value, 0);
}, [items]);
```

## State Management Best Practices

### 1. Keep State Local
Only lift state up when needed:

```typescript
// ❌ Everything in parent
function App() {
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  
  return (
    <>
      <Input value={input1} onChange={setInput1} />
      <Input value={input2} onChange={setInput2} />
    </>
  );
}

// ✅ Local state when possible
function Input() {
  const [value, setValue] = useState('');
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}
```

### 2. Group Related State
```typescript
// ❌ Separate states
const [name, setName] = useState('');
const [email, setEmail] = useState('');
const [age, setAge] = useState(0);

// ✅ Group related data
const [user, setUser] = useState({
  name: '',
  email: '',
  age: 0
});
```

### 3. Avoid Redundant State
```typescript
// ❌ Redundant state
const [items, setItems] = useState([]);
const [itemCount, setItemCount] = useState(0); // Redundant!

// ✅ Derive from existing state
const [items, setItems] = useState([]);
const itemCount = items.length; // Calculated
```

### 4. Reset State When Needed
```typescript
const [messages, setMessages] = useState([]);

const clearChat = () => {
  setMessages([]);
  localStorage.removeItem('chat-messages');
};
```

## Our Complete State Flow

Here's how state flows through our chat application:

```typescript
export const ChatContainer = () => {
  // State declarations
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Load saved messages on mount
  useEffect(() => {
    const saved = localStorage.getItem('chat-messages');
    if (saved) {
      setMessages(JSON.parse(saved));
    }
  }, []);
  
  // Save messages when they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]);
  
  // Handle sending message
  const handleSendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      // API call
      const response = await fetch('/api/process', {
        method: 'POST',
        body: JSON.stringify({ query: content }),
      });
      
      const data = await response.json();
      
      // Add assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: data.content,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Handle error
      console.error('Failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Render
  return (
    <div>
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};
```

## Common State Pitfalls

### 1. Stale Closures
```typescript
// ❌ Problem: count in setTimeout is stale
const [count, setCount] = useState(0);

const incrementLater = () => {
  setTimeout(() => {
    setCount(count + 1); // Uses old count value
  }, 1000);
};

// ✅ Solution: Use functional update
const incrementLater = () => {
  setTimeout(() => {
    setCount(prev => prev + 1); // Always uses latest
  }, 1000);
};
```

### 2. Missing Dependencies
```typescript
// ❌ ESLint warning: missing dependency
useEffect(() => {
  console.log(count);
}, []); // count not in dependencies

// ✅ Include all dependencies
useEffect(() => {
  console.log(count);
}, [count]);
```

### 3. Infinite Loops
```typescript
// ❌ Infinite loop
useEffect(() => {
  setCount(count + 1); // Changes state
}); // No dependency array = runs every render

// ✅ Control when it runs
useEffect(() => {
  setCount(prev => prev + 1);
}, []); // Only on mount
```

### 4. Async in useEffect
```typescript
// ❌ Can't make useEffect async
useEffect(async () => {
  const data = await fetchData();
}, []);

// ✅ Use async function inside
useEffect(() => {
  const loadData = async () => {
    const data = await fetchData();
    setData(data);
  };
  
  loadData();
}, []);
```

## Performance Optimization

### When to Optimize
1. **Measure first** - Use React DevTools Profiler
2. **Optimize expensive computations** - useMemo
3. **Prevent unnecessary renders** - useCallback, memo
4. **Split large components** - Smaller render scope

### Our Optimizations
```typescript
// Memoize callback to prevent ChatInput re-renders
const handleSendMessage = useCallback(async (content: string) => {
  // Implementation
}, []); // No dependencies, never changes

// Auto-scroll optimization
useEffect(() => {
  // Only scroll if new message added
  if (messages.length > previousLength) {
    scrollToBottom();
  }
}, [messages.length]);
```

## State Management Libraries

For larger apps, consider:
- **Zustand** - Simple, lightweight
- **Redux Toolkit** - Industry standard
- **Jotai** - Atomic state management
- **Valtio** - Proxy-based state

Our app is simple enough to use React's built-in state.

## Summary

State management in React:
1. **useState** for component state
2. **useEffect** for side effects
3. **Functional updates** for state based on previous
4. **Dependency arrays** control when effects run
5. **Cleanup functions** prevent memory leaks

Key patterns in our chat:
- Message array state
- Loading/error states
- Local storage persistence
- Auto-scroll on new messages
- Controlled input components

---

**Previous**: [05-typescript-basics.md](./05-typescript-basics.md) | **Next**: [07-building-chat-ui.md](./07-building-chat-ui.md)