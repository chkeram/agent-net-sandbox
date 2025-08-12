# Understanding React Components

## What is a Component?

A React component is a **reusable piece of UI**. Think of it like a custom HTML element that you create. Components can be as small as a button or as large as an entire page.

## Your First Component

Let's look at the simplest possible component:

```tsx
// frontend/src/components/Hello.tsx
function Hello() {
  return <h1>Hello World!</h1>;
}

export default Hello;
```

**Key Points:**
- It's just a JavaScript function
- It returns JSX (looks like HTML)
- The function name starts with a capital letter

## JSX: JavaScript + XML

JSX lets you write HTML-like code in JavaScript:

```tsx
// This JSX:
<div className="container">
  <h1>Title</h1>
  <p>Content</p>
</div>

// Compiles to this JavaScript:
React.createElement('div', { className: 'container' },
  React.createElement('h1', null, 'Title'),
  React.createElement('p', null, 'Content')
)
```

### JSX Rules

1. **Single Root Element**
```tsx
// ❌ Can't return multiple elements
return (
  <h1>Title</h1>
  <p>Content</p>
);

// ✅ Wrap in a parent
return (
  <div>
    <h1>Title</h1>
    <p>Content</p>
  </div>
);

// ✅ Or use Fragment (empty wrapper)
return (
  <>
    <h1>Title</h1>
    <p>Content</p>
  </>
);
```

2. **className, not class**
```tsx
// ❌ HTML attribute
<div class="container">

// ✅ JSX attribute
<div className="container">
```

3. **Close All Tags**
```tsx
// ❌ HTML style
<img src="pic.jpg">
<br>

// ✅ JSX style
<img src="pic.jpg" />
<br />
```

4. **JavaScript in Curly Braces**
```tsx
const name = "John";
const age = 25;

return (
  <div>
    <h1>Hello {name}!</h1>
    <p>You are {age} years old</p>
    <p>Next year you'll be {age + 1}</p>
  </div>
);
```

## Component Props

Props are how you pass data to components. They're like function parameters:

```tsx
// Define what props the component accepts
interface GreetingProps {
  name: string;
  age?: number; // ? means optional
}

// Use the props
function Greeting({ name, age }: GreetingProps) {
  return (
    <div>
      <h1>Hello {name}!</h1>
      {age && <p>You are {age} years old</p>}
    </div>
  );
}

// Using the component
<Greeting name="Alice" age={30} />
<Greeting name="Bob" /> // age is optional
```

## Our Real Chat Components

Let's examine the actual components we built:

### 1. Message Component (`Message.tsx`)

```tsx
import type { Message as MessageType } from '../../types/chat.ts';

interface MessageProps {
  message: MessageType;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={isUser ? 'bg-white' : 'bg-gray-50'}>
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full">
        {isUser ? <User /> : <Bot />}
      </div>
      
      {/* Message content */}
      <div>
        <span>{isUser ? 'You' : 'Assistant'}</span>
        <div>{message.content}</div>
      </div>
    </div>
  );
};
```

**What's happening:**
1. Accepts a `message` prop with TypeScript type
2. Determines if it's a user or assistant message
3. Conditionally renders different styles and icons
4. Returns JSX structure for the message

### 2. MessageList Component (`MessageList.tsx`)

```tsx
interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isLoading 
}) => {
  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        // Show welcome message when empty
        <div>Welcome!</div>
      ) : (
        // Map over messages and render each one
        messages.map((message) => (
          <Message key={message.id} message={message} />
        ))
      )}
    </div>
  );
};
```

**Key Concepts:**
- **Conditional Rendering**: Show different content based on state
- **Lists**: Use `.map()` to render arrays
- **Keys**: Each list item needs a unique `key` prop

### 3. ChatInput Component (`ChatInput.tsx`)

```tsx
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isLoading 
}) => {
  const [input, setInput] = useState('');
  
  const handleSubmit = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput(''); // Clear input after sending
    }
  };
  
  return (
    <div>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={isLoading}
      />
      <button onClick={handleSubmit}>Send</button>
    </div>
  );
};
```

**Important Patterns:**
- **Controlled Components**: Input value tied to state
- **Event Handlers**: Respond to user interactions
- **Callback Props**: Send data back to parent

## Component Composition

Components can use other components, creating a hierarchy:

```tsx
// ChatContainer uses multiple child components
function ChatContainer() {
  const [messages, setMessages] = useState([]);
  
  const handleSendMessage = (text: string) => {
    // Add message to state
  };
  
  return (
    <div>
      <MessageList messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}
```

**Component Tree:**
```
App
└── ChatContainer
    ├── MessageList
    │   └── Message (multiple)
    └── ChatInput
```

## Props vs State

### Props
- Data passed **from parent to child**
- **Read-only** (can't modify)
- Component **receives** them

```tsx
// Parent passes props down
<Message content="Hello" isUser={true} />

// Child receives props
function Message({ content, isUser }) {
  // Can't do: content = "Modified" ❌
  return <div>{content}</div>;
}
```

### State
- Data that **belongs to** the component
- **Can be modified** by the component
- Changes trigger re-renders

```tsx
function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

## Component Lifecycle

React components go through these phases:

1. **Mount** - Component appears on screen
2. **Update** - Component re-renders (props/state change)
3. **Unmount** - Component removed from screen

```tsx
function MyComponent() {
  // Runs after mount and updates
  useEffect(() => {
    console.log('Component rendered');
    
    // Cleanup function runs on unmount
    return () => {
      console.log('Component unmounting');
    };
  }, []); // Empty array = run once on mount
  
  return <div>Hello</div>;
}
```

## Event Handling

React uses synthetic events (cross-browser compatible):

```tsx
function Button() {
  // Event handler function
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent default behavior
    console.log('Clicked!');
  };
  
  return (
    <button onClick={handleClick}>
      Click me
    </button>
  );
}
```

**Common Events:**
- `onClick` - Mouse click
- `onChange` - Input value changes
- `onSubmit` - Form submission
- `onKeyDown` - Keyboard key pressed
- `onFocus` / `onBlur` - Focus events

## Conditional Rendering Patterns

### 1. Ternary Operator
```tsx
{isLoggedIn ? <Dashboard /> : <Login />}
```

### 2. Logical AND
```tsx
{isLoading && <Spinner />}
```

### 3. Early Return
```tsx
function Component({ user }) {
  if (!user) {
    return <div>Please log in</div>;
  }
  
  return <div>Welcome {user.name}</div>;
}
```

## Lists and Keys

When rendering lists, each item needs a unique `key`:

```tsx
function TodoList({ todos }) {
  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}> {/* Unique key */}
          {todo.text}
        </li>
      ))}
    </ul>
  );
}
```

**Why Keys Matter:**
- React uses keys to track which items changed
- Helps with performance and maintaining state
- Use stable, unique IDs (not array index)

## Component Best Practices

### 1. Single Responsibility
Each component should do one thing well:

```tsx
// ✅ Good: Focused components
<MessageList />
<MessageInput />
<MessageAvatar />

// ❌ Bad: Does too much
<MessageListWithInputAndAvatarAndEverything />
```

### 2. Props Interface
Always define prop types with TypeScript:

```tsx
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}
```

### 3. Descriptive Names
```tsx
// ✅ Good names
<UserAvatar />
<MessageList />
<SendButton />

// ❌ Vague names
<Thing />
<Comp />
<Btn />
```

### 4. Consistent Structure
```tsx
// 1. Imports
import React from 'react';
import { Icon } from 'lucide-react';

// 2. Types/Interfaces
interface Props { }

// 3. Component
export const Component: React.FC<Props> = () => {
  // 4. Hooks
  const [state, setState] = useState();
  
  // 5. Handlers
  const handleClick = () => { };
  
  // 6. Render
  return <div>...</div>;
};
```

## Understanding Our Chat Architecture

Here's how our chat components work together:

```
ChatContainer (State Manager)
    ↓ messages array
MessageList (Display)
    ↓ individual message
Message (Presentation)

ChatContainer (State Manager)
    ↓ handleSendMessage callback
ChatInput (User Input)
    ↑ sends message text back
```

**Data Flow:**
1. User types in `ChatInput`
2. User clicks send
3. `ChatInput` calls `onSendMessage` callback
4. `ChatContainer` updates messages state
5. New message passes to `MessageList`
6. `MessageList` renders new `Message`

## Common Pitfalls

### 1. Modifying Props
```tsx
// ❌ Never modify props
function Bad({ user }) {
  user.name = "Modified"; // ERROR!
  return <div>{user.name}</div>;
}

// ✅ Create new object
function Good({ user }) {
  const modifiedUser = { ...user, name: "Modified" };
  return <div>{modifiedUser.name}</div>;
}
```

### 2. Missing Keys in Lists
```tsx
// ❌ No key or using index
{items.map((item, index) => (
  <Item key={index} /> // Bad: index can change
))}

// ✅ Use stable unique ID
{items.map((item) => (
  <Item key={item.id} /> // Good: ID is stable
))}
```

### 3. State Updates
```tsx
// ❌ Direct mutation
const [items, setItems] = useState([1, 2, 3]);
items.push(4); // Doesn't trigger re-render!

// ✅ Create new array
setItems([...items, 4]); // Triggers re-render
```

## Practice Exercises

1. **Create a Counter Component**
   - Shows a number
   - Has increment/decrement buttons
   - Can't go below 0

2. **Build a Todo Item**
   - Shows text
   - Has checkbox
   - Can be deleted
   - Strikethrough when completed

3. **Make a User Card**
   - Shows name and avatar
   - Has online/offline status
   - Click to show more details

## Summary

Components are the building blocks of React applications. They:
- Encapsulate UI and logic
- Accept props for customization
- Manage their own state
- Can be composed together
- Follow predictable patterns

Next, we'll learn how to style these components with Tailwind CSS!

---

**Previous**: [02-project-setup.md](./02-project-setup.md) | **Next**: [04-styling-with-tailwind.md](./04-styling-with-tailwind.md)