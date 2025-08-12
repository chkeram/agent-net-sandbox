# TypeScript Basics for React

## Why TypeScript?

TypeScript adds **type safety** to JavaScript, catching errors before your code runs. It's like having a proofreader for your code.

### JavaScript vs TypeScript

**JavaScript (runtime errors):**
```javascript
function greet(user) {
  return "Hello " + user.name.toUpperCase();
}

greet(); // 💥 Crashes at runtime: Cannot read property 'name' of undefined
```

**TypeScript (compile-time errors):**
```typescript
interface User {
  name: string;
}

function greet(user: User): string {
  return "Hello " + user.name.toUpperCase();
}

greet(); // ❌ Error at compile time: Expected 1 argument, but got 0
```

## Basic Types

### Primitive Types

```typescript
// Basic types
let name: string = "Alice";
let age: number = 30;
let isActive: boolean = true;
let nothing: null = null;
let notDefined: undefined = undefined;

// Arrays
let numbers: number[] = [1, 2, 3];
let names: string[] = ["Alice", "Bob"];
let mixed: (string | number)[] = ["Alice", 30];

// Alternative array syntax
let scores: Array<number> = [100, 95, 87];
```

### Object Types

```typescript
// Object with inline type
let user: { name: string; age: number } = {
  name: "Alice",
  age: 30
};

// Using interface (preferred)
interface User {
  name: string;
  age: number;
  email?: string; // Optional property
}

let alice: User = {
  name: "Alice",
  age: 30
  // email is optional
};
```

## Interfaces vs Types

Both `interface` and `type` can define object shapes, but they have differences:

### Interface (Preferred for Objects)
```typescript
interface Message {
  id: string;
  content: string;
  timestamp: Date;
}

// Can be extended
interface UserMessage extends Message {
  userId: string;
}

// Can be merged (declaration merging)
interface User {
  name: string;
}
interface User {
  age: number; // Adds to the same interface
}
```

### Type Aliases (More Flexible)
```typescript
// Can create union types
type Status = 'pending' | 'active' | 'completed';

// Can create intersection types
type WithId = { id: string };
type WithTimestamp = { timestamp: Date };
type Document = WithId & WithTimestamp & {
  content: string;
};

// Can't be merged like interfaces
```

## Our Chat Types Explained

Let's examine the actual TypeScript types we use:

### Message Interface (`types/chat.ts`)
```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';  // Union type
  content: string;
  timestamp: Date;
  agentId?: string;      // Optional
  agentName?: string;    // Optional
  protocol?: string;     // Optional
  confidence?: number;   // Optional
  isStreaming?: boolean; // Optional
  error?: string;        // Optional
}
```

**Key Concepts:**
- **Union Types**: `role` can only be one of three strings
- **Optional Properties**: Use `?` for properties that might not exist
- **Export**: Makes the interface available to other files

### Agent Types (`types/agent.ts`)
```typescript
export interface Agent {
  agent_id: string;
  name: string;
  protocol: 'acp' | 'a2a' | 'mcp' | 'custom';
  status: 'healthy' | 'degraded' | 'unhealthy';
  capabilities: string[];  // Array of strings
  endpoint: string;
  last_seen: Date;
  description?: string;
}

export interface RoutingDecision {
  selected_agent: Agent | null;  // Can be Agent or null
  confidence: number;
  reasoning: string;
  fallback_agents?: Agent[];     // Optional array
}
```

## Function Types

### Basic Function Types
```typescript
// Function type annotation
function add(a: number, b: number): number {
  return a + b;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Function as a type
type MathOperation = (a: number, b: number) => number;
const subtract: MathOperation = (a, b) => a - b;

// Optional parameters
function greet(name: string, title?: string): string {
  if (title) {
    return `Hello, ${title} ${name}`;
  }
  return `Hello, ${name}`;
}

// Default parameters
function createUser(name: string, age: number = 18): User {
  return { name, age };
}
```

### Callback Types
```typescript
// Our ChatInput component
interface ChatInputProps {
  onSendMessage: (message: string) => void;  // Callback type
  isLoading?: boolean;
}

// Using the callback
const handleSend = (text: string): void => {
  console.log("Sending:", text);
};

<ChatInput onSendMessage={handleSend} />
```

## React Component Types

### Functional Component Types
```typescript
import { FC, ReactNode } from 'react';

// Method 1: Using FC (Function Component)
interface ButtonProps {
  label: string;
  onClick: () => void;
}

const Button: FC<ButtonProps> = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};

// Method 2: Direct typing (preferred in our project)
export const Button = ({ label, onClick }: ButtonProps) => {
  return <button onClick={onClick}>{label}</button>;
};

// Children props
interface ContainerProps {
  children: ReactNode;  // Can be any valid React content
}

const Container = ({ children }: ContainerProps) => {
  return <div className="container">{children}</div>;
};
```

### Event Types
```typescript
import { ChangeEvent, MouseEvent, KeyboardEvent, FormEvent } from 'react';

// Input change event
const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
  console.log(e.target.value);
};

// Textarea change (different element type)
const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
  console.log(e.target.value);
};

// Button click
const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
  e.preventDefault();
  console.log('Clicked!');
};

// Keyboard event
const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
  if (e.key === 'Enter') {
    console.log('Enter pressed');
  }
};

// Form submission
const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // Process form
};
```

## Generic Types

Generics make components and functions reusable with different types:

### Basic Generics
```typescript
// Generic function
function identity<T>(value: T): T {
  return value;
}

identity<string>("hello");  // T is string
identity<number>(42);        // T is number

// Generic interface
interface Box<T> {
  value: T;
}

const stringBox: Box<string> = { value: "hello" };
const numberBox: Box<number> = { value: 42 };
```

### React State with Generics
```typescript
import { useState } from 'react';

// useState is generic
const [message, setMessage] = useState<string>("");
const [count, setCount] = useState<number>(0);
const [user, setUser] = useState<User | null>(null);

// Array state
const [messages, setMessages] = useState<Message[]>([]);

// Our actual usage
export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // TypeScript knows messages is Message[]
  messages.map(msg => msg.content);  // ✅ TypeScript knows msg has content
};
```

## Type Assertions and Guards

### Type Assertions
```typescript
// When you know more than TypeScript
const input = document.getElementById('myInput') as HTMLInputElement;
input.value = "Hello";  // TypeScript knows it's an input

// Alternative syntax (avoid)
const input2 = <HTMLInputElement>document.getElementById('myInput');

// Our example: parsing JSON
const data = JSON.parse(response) as Message;
```

### Type Guards
```typescript
// typeof guard
function processValue(value: string | number) {
  if (typeof value === 'string') {
    // TypeScript knows value is string here
    return value.toUpperCase();
  } else {
    // TypeScript knows value is number here
    return value * 2;
  }
}

// in operator
interface User {
  name: string;
  email?: string;
}

function hasEmail(user: User): boolean {
  return 'email' in user;
}

// Custom type guard
function isMessage(obj: any): obj is Message {
  return obj && 
         typeof obj.id === 'string' &&
         typeof obj.content === 'string';
}

// Usage
if (isMessage(data)) {
  // TypeScript knows data is Message here
  console.log(data.content);
}
```

## Utility Types

TypeScript provides built-in utility types:

### Common Utility Types
```typescript
interface User {
  id: string;
  name: string;
  email: string;
  age: number;
}

// Partial: All properties optional
type PartialUser = Partial<User>;
// { id?: string; name?: string; email?: string; age?: number }

// Required: All properties required
type RequiredUser = Required<PartialUser>;

// Pick: Select specific properties
type UserSummary = Pick<User, 'id' | 'name'>;
// { id: string; name: string }

// Omit: Exclude properties
type UserWithoutEmail = Omit<User, 'email'>;
// { id: string; name: string; age: number }

// Readonly: Make immutable
type ReadonlyUser = Readonly<User>;
// All properties are readonly
```

### Our Usage Examples
```typescript
// Making a form data type from our Message interface
type MessageFormData = Pick<Message, 'content' | 'role'>;

// Update function that accepts partial data
function updateMessage(id: string, updates: Partial<Message>) {
  // Can update any subset of Message properties
}

// Creating a draft message
type DraftMessage = Omit<Message, 'id' | 'timestamp'>;
```

## Type Imports

TypeScript distinguishes between value and type imports:

```typescript
// Regular import (for values)
import { ChatContainer } from './ChatContainer.tsx';

// Type-only import (removed at compile time)
import type { Message } from './types/chat.ts';

// Mixed import (avoid if possible)
import React, { type FC } from 'react';

// Our actual usage
import type { Message as MessageType } from '../../types/chat.ts';
```

**Why use type imports?**
- Clearer intent
- Better tree-shaking
- Required with `verbatimModuleSyntax` in tsconfig

## Common TypeScript Patterns in React

### Props with Children
```typescript
interface LayoutProps {
  children: ReactNode;
  title?: string;
}

const Layout = ({ children, title }: LayoutProps) => (
  <div>
    {title && <h1>{title}</h1>}
    {children}
  </div>
);
```

### Conditional Props
```typescript
type ButtonProps = {
  label: string;
} & (
  | { variant: 'link'; href: string }
  | { variant: 'button'; onClick: () => void }
);

const Button = (props: ButtonProps) => {
  if (props.variant === 'link') {
    return <a href={props.href}>{props.label}</a>;
  }
  return <button onClick={props.onClick}>{props.label}</button>;
};
```

### Component with Ref
```typescript
import { forwardRef } from 'react';

interface InputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, value, onChange }, ref) => (
    <div>
      <label>{label}</label>
      <input 
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
);
```

## TypeScript Configuration

Our `tsconfig.app.json` explained:

```json
{
  "compilerOptions": {
    "target": "ES2022",        // Output modern JavaScript
    "lib": ["ES2022", "DOM"],  // Available libraries
    "jsx": "react-jsx",        // JSX handling
    "strict": true,            // Enable all strict checks
    
    // Strict checks included:
    "noImplicitAny": true,     // Error on 'any' type
    "strictNullChecks": true,  // Check for null/undefined
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    
    // Module settings
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,  // Require .ts in imports
    "verbatimModuleSyntax": true,       // Require type imports
  }
}
```

## Common TypeScript Errors and Solutions

### Error: "Object is possibly 'undefined'"
```typescript
// Problem
interface Props {
  user?: User;
}
const Component = ({ user }: Props) => {
  return <div>{user.name}</div>;  // ❌ user might be undefined
};

// Solution 1: Optional chaining
return <div>{user?.name}</div>;

// Solution 2: Guard
if (user) {
  return <div>{user.name}</div>;
}

// Solution 3: Default value
const Component = ({ user = defaultUser }: Props) => {
```

### Error: "Type 'string | undefined' is not assignable to type 'string'"
```typescript
// Problem
const value: string | undefined = getValue();
const uppercased: string = value.toUpperCase(); // ❌

// Solution
const uppercased: string = value?.toUpperCase() ?? '';
```

### Error: "Property does not exist on type"
```typescript
// Problem
const data = { name: "Alice" };
console.log(data.age); // ❌ Property 'age' does not exist

// Solution: Define the type
interface Person {
  name: string;
  age?: number;
}
const data: Person = { name: "Alice" };
```

## Best Practices

1. **Use interfaces for objects**
   ```typescript
   interface User { }  // ✅
   type User = { }     // Works but interface preferred
   ```

2. **Avoid `any` type**
   ```typescript
   let data: any;      // ❌ Loses type safety
   let data: unknown;  // ✅ Safe alternative
   ```

3. **Use const assertions for literals**
   ```typescript
   const ROLES = ['user', 'admin'] as const;
   type Role = typeof ROLES[number]; // 'user' | 'admin'
   ```

4. **Prefer type inference when obvious**
   ```typescript
   const name = "Alice";  // TypeScript knows it's string
   const name: string = "Alice";  // Redundant
   ```

5. **Use discriminated unions**
   ```typescript
   type Result = 
     | { success: true; data: string }
     | { success: false; error: string };
   ```

## Summary

TypeScript in React provides:
- **Compile-time error checking**
- **Better IDE support** (autocomplete, refactoring)
- **Self-documenting code** through types
- **Safer refactoring** with confidence

Key concepts for our chat app:
- Interfaces for component props
- Type-only imports for better performance
- Optional properties for flexible APIs
- Union types for constrained values
- Generics for reusable components

---

**Previous**: [04-styling-with-tailwind.md](./04-styling-with-tailwind.md) | **Next**: [06-state-management.md](./06-state-management.md)