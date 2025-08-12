# Advanced Features: Message Actions System

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build a professional message actions system (copy, regenerate, delete, etc.)
- Understand clipboard integration and browser API considerations
- Implement context-aware actions based on message state
- Create extensible action architecture for future features
- Master accessibility patterns for action buttons

## 🎨 **What Are Message Actions?**

Message actions are the small buttons that appear on messages, allowing users to interact with content:

```
┌─────────────────────────────────────────┐
│ 🤖 Assistant                           │
│                                         │
│ The answer is 42.                       │
│                                         │
│ 🎯 Routing Decision → Math Agent (95%)  │
│                                         │
│ [📋 Copy] [🔄 Regenerate]              │  ← Message Actions
└─────────────────────────────────────────┘
```

### **Common Message Actions**
- **Copy**: Copy message content to clipboard
- **Regenerate**: Re-run the original user query for a new response
- **Delete**: Remove message from conversation
- **Edit**: Modify the message content
- **Share**: Share message via URL or export
- **Bookmark**: Save for later reference
- **Report**: Flag inappropriate content

## 🏗️ **Action System Architecture**

Our message actions follow a **command pattern** with contextual availability:

```typescript
// src/types/messageActions.ts
export interface MessageAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  handler: (message: Message) => void | Promise<void>;
  isVisible: (message: Message, user?: User) => boolean;
  isDisabled: (message: Message, appState?: AppState) => boolean;
  shortcut?: string;
  tooltip?: string;
  destructive?: boolean; // For delete, clear actions
}

export interface MessageActionsConfig {
  alwaysVisible?: boolean;     // Show without hover
  position?: 'top' | 'bottom' | 'inline';
  maxActions?: number;         // Show only first N actions
  showLabels?: boolean;        // Show text labels or just icons
  compact?: boolean;           // Smaller buttons
}
```

## 🛠️ **Core Actions Implementation**

### **Step 1: Base Action Definitions**

```typescript
// src/actions/messageActions.ts
import { Copy, RotateCcw, Trash2, Edit3, Share, Bookmark } from 'lucide-react';
import type { Message } from '../types/chat';

export const createCopyAction = (onCopy: (content: string) => void): MessageAction => ({
  id: 'copy',
  label: 'Copy',
  icon: Copy,
  tooltip: 'Copy message to clipboard',
  shortcut: 'Ctrl+C',
  handler: async (message: Message) => {
    if (message.content) {
      onCopy(message.content);
    }
  },
  isVisible: (message: Message) => {
    // Show copy for any message with content
    return !!message.content && message.content.trim().length > 0;
  },
  isDisabled: (message: Message) => {
    // Disable if no content or currently streaming
    return !message.content || !!message.isStreaming;
  },
});

export const createRegenerateAction = (onRegenerate: (messageId: string) => void): MessageAction => ({
  id: 'regenerate', 
  label: 'Regenerate',
  icon: RotateCcw,
  tooltip: 'Generate a new response',
  shortcut: 'Ctrl+R',
  handler: async (message: Message) => {
    onRegenerate(message.id);
  },
  isVisible: (message: Message) => {
    // Only show for assistant messages (not user messages)
    return message.role === 'assistant';
  },
  isDisabled: (message: Message, appState?: AppState) => {
    // Disable during streaming or if app is busy
    return !!message.isStreaming || appState?.isLoading || false;
  },
});

export const createDeleteAction = (onDelete: (messageId: string) => void): MessageAction => ({
  id: 'delete',
  label: 'Delete',
  icon: Trash2,
  tooltip: 'Delete this message',
  destructive: true,
  handler: async (message: Message) => {
    // Confirm destructive action
    if (window.confirm('Are you sure you want to delete this message?')) {
      onDelete(message.id);
    }
  },
  isVisible: (message: Message) => {
    // Show delete for any message
    return true;
  },
  isDisabled: (message: Message) => {
    // Disable during streaming
    return !!message.isStreaming;
  },
});
```

### **Step 2: Action Registry System**

```typescript
// src/services/actionRegistry.ts
class MessageActionRegistry {
  private actions = new Map<string, MessageAction>();
  private contextProviders = new Map<string, () => any>();
  
  registerAction(action: MessageAction): void {
    this.actions.set(action.id, action);
  }
  
  unregisterAction(actionId: string): void {
    this.actions.delete(actionId);
  }
  
  getActions(message: Message, config: MessageActionsConfig = {}): MessageAction[] {
    const allActions = Array.from(this.actions.values());
    
    // Filter by visibility
    const visibleActions = allActions.filter(action => 
      action.isVisible(message)
    );
    
    // Sort by priority (copy first, destructive last)
    const sortedActions = visibleActions.sort((a, b) => {
      if (a.destructive && !b.destructive) return 1;
      if (!a.destructive && b.destructive) return -1;
      if (a.id === 'copy') return -1;
      if (b.id === 'copy') return 1;
      return 0;
    });
    
    // Limit number of actions if specified
    if (config.maxActions) {
      return sortedActions.slice(0, config.maxActions);
    }
    
    return sortedActions;
  }
  
  executeAction(actionId: string, message: Message): Promise<void> {
    const action = this.actions.get(actionId);
    if (!action) {
      throw new Error(`Action ${actionId} not found`);
    }
    
    if (action.isDisabled(message)) {
      console.warn(`Action ${actionId} is disabled for this message`);
      return Promise.resolve();
    }
    
    return Promise.resolve(action.handler(message));
  }
  
  // Context providers for complex state management
  addContextProvider(key: string, provider: () => any): void {
    this.contextProviders.set(key, provider);
  }
  
  getContext(key: string): any {
    const provider = this.contextProviders.get(key);
    return provider ? provider() : undefined;
  }
}

export const messageActionRegistry = new MessageActionRegistry();
```

### **Step 3: MessageActions Component**

```typescript
// src/components/Chat/MessageActions.tsx
import React from 'react';
import { MessageAction, MessageActionsConfig } from '../../types/messageActions';
import { messageActionRegistry } from '../../services/actionRegistry';
import type { Message } from '../../types/chat';

interface MessageActionsProps {
  message: Message;
  config?: MessageActionsConfig;
  className?: string;
}

export const MessageActions: React.FC<MessageActionsProps> = ({
  message,
  config = {},
  className = '',
}) => {
  const actions = messageActionRegistry.getActions(message, config);
  
  if (actions.length === 0) {
    return null;
  }
  
  const handleActionClick = async (action: MessageAction, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    try {
      await messageActionRegistry.executeAction(action.id, message);
    } catch (error) {
      console.error(`Failed to execute action ${action.id}:`, error);
      // Could show toast notification here
    }
  };
  
  const baseClasses = config.compact 
    ? 'flex items-center gap-1' 
    : 'flex items-center gap-2';
    
  const buttonClasses = config.compact
    ? 'p-1 text-xs'
    : 'px-2 py-1 text-xs';
  
  return (
    <div className={`${baseClasses} ${className} ${!config.alwaysVisible ? 'opacity-0 group-hover:opacity-100' : ''} transition-opacity`}>
      {actions.map((action) => {
        const Icon = action.icon;
        const isDisabled = action.isDisabled(message);
        
        return (
          <button
            key={action.id}
            onClick={(e) => handleActionClick(action, e)}
            disabled={isDisabled}
            title={action.tooltip || action.label}
            className={`
              ${buttonClasses}
              flex items-center gap-1
              text-gray-500 hover:text-gray-700 
              dark:text-gray-400 dark:hover:text-gray-200
              hover:bg-gray-100 dark:hover:bg-gray-700 
              rounded transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
              ${action.destructive ? 'hover:text-red-600 hover:bg-red-50 dark:hover:text-red-400 dark:hover:bg-red-900/20' : ''}
            `}
          >
            <Icon className="w-3 h-3" />
            {config.showLabels && (
              <span className="hidden sm:inline">{action.label}</span>
            )}
          </button>
        );
      })}
    </div>
  );
};
```

## 📋 **Clipboard Integration**

Modern clipboard integration requires careful handling of different content types and browser permissions:

### **Advanced Clipboard Service**

```typescript
// src/services/clipboardService.ts
interface ClipboardOptions {
  showFeedback?: boolean;
  feedbackDuration?: number;
  format?: 'plain' | 'html' | 'markdown';
}

class ClipboardService {
  async copyText(text: string, options: ClipboardOptions = {}): Promise<boolean> {
    try {
      // Try modern Clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        this.showFeedback('Copied to clipboard!', options);
        return true;
      }
      
      // Fallback to legacy method
      return this.legacyCopyText(text, options);
      
    } catch (error) {
      console.error('Failed to copy text:', error);
      this.showFeedback('Failed to copy to clipboard', { ...options, isError: true });
      return false;
    }
  }
  
  async copyRich(content: { text: string; html?: string; markdown?: string }, options: ClipboardOptions = {}): Promise<boolean> {
    try {
      if (navigator.clipboard && navigator.clipboard.write) {
        const clipboardItems: ClipboardItem[] = [];
        
        // Add text content
        if (content.text) {
          clipboardItems.push(
            new ClipboardItem({
              'text/plain': new Blob([content.text], { type: 'text/plain' }),
            })
          );
        }
        
        // Add HTML content if available
        if (content.html) {
          clipboardItems.push(
            new ClipboardItem({
              'text/html': new Blob([content.html], { type: 'text/html' }),
            })
          );
        }
        
        await navigator.clipboard.write(clipboardItems);
        this.showFeedback('Rich content copied!', options);
        return true;
      }
      
      // Fallback to plain text
      return this.copyText(content.text, options);
      
    } catch (error) {
      console.error('Failed to copy rich content:', error);
      return this.copyText(content.text, options);
    }
  }
  
  private legacyCopyText(text: string, options: ClipboardOptions): boolean {
    try {
      // Create temporary textarea
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      textarea.style.pointerEvents = 'none';
      
      document.body.appendChild(textarea);
      textarea.select();
      textarea.setSelectionRange(0, text.length);
      
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      
      if (success) {
        this.showFeedback('Copied to clipboard!', options);
      } else {
        this.showFeedback('Failed to copy', { ...options, isError: true });
      }
      
      return success;
      
    } catch (error) {
      console.error('Legacy copy failed:', error);
      return false;
    }
  }
  
  async checkPermission(): Promise<'granted' | 'denied' | 'prompt'> {
    try {
      if (navigator.permissions && navigator.permissions.query) {
        const permission = await navigator.permissions.query({ name: 'clipboard-write' as PermissionName });
        return permission.state as 'granted' | 'denied' | 'prompt';
      }
      
      // If permissions API not available, assume granted for basic clipboard access
      return 'granted';
      
    } catch (error) {
      console.warn('Could not check clipboard permission:', error);
      return 'prompt';
    }
  }
  
  private showFeedback(message: string, options: ClipboardOptions & { isError?: boolean } = {}): void {
    if (options.showFeedback === false) return;
    
    // Simple toast notification (you could use a more sophisticated system)
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.className = `
      fixed bottom-4 right-4 z-50
      px-4 py-2 rounded-lg text-sm font-medium
      ${options.isError 
        ? 'bg-red-600 text-white' 
        : 'bg-green-600 text-white'
      }
      transform transition-all duration-300 ease-in-out
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    });
    
    // Remove after delay
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      toast.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, options.feedbackDuration || 2000);
  }
}

export const clipboardService = new ClipboardService();
```

### **Message Content Formatting**

```typescript
// src/utils/messageFormatting.ts
export class MessageFormatter {
  static toPlainText(message: Message): string {
    // Strip markdown and return clean text
    return message.content
      .replace(/```[\s\S]*?```/g, '') // Remove code blocks
      .replace(/`([^`]+)`/g, '$1')     // Remove inline code
      .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
      .replace(/\*([^*]+)\*/g, '$1')     // Remove italic
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
      .replace(/^#+\s+/gm, '')         // Remove headers
      .trim();
  }
  
  static toMarkdown(message: Message): string {
    let content = `**${message.role === 'user' ? 'User' : message.agentName || 'Assistant'}**: ${message.content}\n\n`;
    
    if (message.reasoning && message.confidence) {
      content += `*Routing: ${message.agentName} (${Math.round(message.confidence * 100)}% confidence)*\n`;
      content += `*Reasoning: ${message.reasoning}*\n\n`;
    }
    
    return content;
  }
  
  static toHTML(message: Message): string {
    // Convert markdown to HTML (you might use a library like marked)
    let html = `<div class="message message--${message.role}">`;
    html += `<strong>${message.role === 'user' ? 'User' : message.agentName || 'Assistant'}:</strong> `;
    html += `<div class="message-content">${this.markdownToHtml(message.content)}</div>`;
    
    if (message.reasoning) {
      html += `<div class="message-meta">`;
      html += `<em>Routing: ${message.agentName} (${Math.round(message.confidence! * 100)}% confidence)</em><br>`;
      html += `<em>Reasoning: ${message.reasoning}</em>`;
      html += `</div>`;
    }
    
    html += `</div>`;
    return html;
  }
  
  private static markdownToHtml(markdown: string): string {
    // Simple markdown to HTML conversion
    // In production, use a proper library like marked or remark
    return markdown
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  }
}
```

## 🔧 **Context-Aware Actions**

Different actions should appear based on message state and user permissions:

### **Action Visibility Rules**

```typescript
// src/utils/actionVisibility.ts
export interface ActionContext {
  user?: {
    permissions: string[];
    isAuthenticated: boolean;
  };
  app?: {
    isLoading: boolean;
    isOffline: boolean;
    features: string[];
  };
  conversation?: {
    isShared: boolean;
    isArchived: boolean;
  };
}

export class ActionVisibilityManager {
  static shouldShowAction(
    action: MessageAction, 
    message: Message, 
    context: ActionContext = {}
  ): boolean {
    // Basic visibility check
    if (!action.isVisible(message)) {
      return false;
    }
    
    // Permission-based visibility
    if (action.id === 'delete' && !context.user?.permissions.includes('delete_messages')) {
      return false;
    }
    
    // Feature flag visibility
    if (action.id === 'share' && !context.app?.features.includes('message_sharing')) {
      return false;
    }
    
    // Conversation state visibility
    if (context.conversation?.isArchived && ['regenerate', 'edit'].includes(action.id)) {
      return false;
    }
    
    // Online/offline visibility
    if (context.app?.isOffline && ['regenerate', 'share'].includes(action.id)) {
      return false;
    }
    
    return true;
  }
  
  static getAvailableActions(
    message: Message,
    allActions: MessageAction[],
    context: ActionContext = {}
  ): MessageAction[] {
    return allActions.filter(action => 
      this.shouldShowAction(action, message, context)
    );
  }
}
```

### **Dynamic Action Registration**

```typescript
// src/hooks/useMessageActions.ts
export const useMessageActions = (
  message: Message, 
  handlers: {
    onCopy: (content: string) => void;
    onRegenerate: (messageId: string) => void;
    onDelete: (messageId: string) => void;
  }
) => {
  useEffect(() => {
    // Register actions dynamically
    messageActionRegistry.registerAction(createCopyAction(handlers.onCopy));
    messageActionRegistry.registerAction(createRegenerateAction(handlers.onRegenerate));
    messageActionRegistry.registerAction(createDeleteAction(handlers.onDelete));
    
    // Add context providers
    messageActionRegistry.addContextProvider('app', () => ({
      isLoading: false, // Get from app state
      isOffline: !navigator.onLine,
      features: ['message_sharing', 'message_editing'],
    }));
    
    return () => {
      // Cleanup on unmount
      messageActionRegistry.unregisterAction('copy');
      messageActionRegistry.unregisterAction('regenerate');
      messageActionRegistry.unregisterAction('delete');
    };
  }, [handlers]);
  
  const availableActions = messageActionRegistry.getActions(message);
  
  return {
    actions: availableActions,
    executeAction: (actionId: string) => messageActionRegistry.executeAction(actionId, message),
  };
};
```

## ♿ **Accessibility Considerations**

### **Keyboard Navigation**

```typescript
// src/components/Chat/AccessibleMessageActions.tsx
export const AccessibleMessageActions: React.FC<MessageActionsProps> = ({
  message,
  config = {},
}) => {
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const actionsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const actions = messageActionRegistry.getActions(message, config);
  
  const handleKeyDown = (event: React.KeyboardEvent, actionIndex: number) => {
    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault();
        const nextIndex = (actionIndex + 1) % actions.length;
        actionsRef.current[nextIndex]?.focus();
        setFocusedIndex(nextIndex);
        break;
        
      case 'ArrowLeft':
        event.preventDefault();
        const prevIndex = actionIndex === 0 ? actions.length - 1 : actionIndex - 1;
        actionsRef.current[prevIndex]?.focus();
        setFocusedIndex(prevIndex);
        break;
        
      case 'Home':
        event.preventDefault();
        actionsRef.current[0]?.focus();
        setFocusedIndex(0);
        break;
        
      case 'End':
        event.preventDefault();
        const lastIndex = actions.length - 1;
        actionsRef.current[lastIndex]?.focus();
        setFocusedIndex(lastIndex);
        break;
        
      case 'Enter':
      case ' ':
        event.preventDefault();
        handleActionClick(actions[actionIndex], event as any);
        break;
    }
  };
  
  return (
    <div 
      role="toolbar" 
      aria-label="Message actions"
      className="flex items-center gap-1"
    >
      {actions.map((action, index) => (
        <button
          key={action.id}
          ref={el => actionsRef.current[index] = el}
          onClick={(e) => handleActionClick(action, e)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          disabled={action.isDisabled(message)}
          aria-label={action.tooltip || action.label}
          className={`
            p-2 rounded-md transition-colors
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            ${action.destructive 
              ? 'text-red-600 hover:bg-red-50 focus:ring-red-500' 
              : 'text-gray-600 hover:bg-gray-100'
            }
          `}
        >
          <action.icon className="w-4 h-4" />
          <span className="sr-only">{action.label}</span>
        </button>
      ))}
    </div>
  );
};
```

### **Screen Reader Support**

```typescript
// Add ARIA labels and descriptions
const MessageWithActions: React.FC<{ message: Message }> = ({ message }) => {
  const actionCount = messageActionRegistry.getActions(message).length;
  
  return (
    <div 
      className="message-container group"
      aria-label={`Message from ${message.role === 'user' ? 'user' : message.agentName}`}
      aria-describedby={`actions-${message.id}`}
    >
      <div className="message-content">
        {message.content}
      </div>
      
      <div 
        id={`actions-${message.id}`}
        aria-label={`${actionCount} actions available`}
        className="message-actions"
      >
        <AccessibleMessageActions message={message} />
      </div>
    </div>
  );
};
```

## 🎯 **Key Takeaways**

1. **Actions should be contextual** - Show relevant actions based on message state
2. **Clipboard integration is complex** - Handle permissions, fallbacks, and different content types
3. **Accessibility matters** - Support keyboard navigation and screen readers
4. **Extensibility is valuable** - Design for easy addition of new actions
5. **User feedback is essential** - Show success/failure states for actions
6. **Performance considerations** - Don't re-render actions unnecessarily
7. **Mobile considerations** - Touch-friendly targets and appropriate spacing

## 📋 **Next Steps**

In the next tutorial, we'll explore:
- **Routing Reasoning Display**: Building expandable UI for AI decision transparency
- **Confidence Score Visualization**: Progress bars and color coding
- **Agent Information Cards**: Detailed agent capabilities display
- **Protocol Badge System**: Visual protocol identification

## 🔗 **Helpful Resources**

- [Clipboard API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [React Accessibility](https://react.dev/learn/accessibility)
- [Keyboard Navigation Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)

---

**Next**: [03-routing-reasoning-display.md](./03-routing-reasoning-display.md) - AI Decision Transparency UI

**Previous**: [01-retry-mechanisms.md](./01-retry-mechanisms.md)