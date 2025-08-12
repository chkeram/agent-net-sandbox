# Architecture 3: Component Composition Patterns - Reusable Component Design

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Advanced React component composition patterns used in the Agent Network Sandbox
- How to build flexible, reusable components that scale across the application
- When to use render props, compound components, and higher-order patterns
- TypeScript patterns for component composition and polymorphic components
- Testing strategies for composed components
- Performance optimization techniques for complex component hierarchies

## 🧩 **Component Composition Philosophy**

Our Agent Network Sandbox follows these composition principles:

```
┌─────────────────────────────────────────────┐
│              Presentation Layer              │ ← Pure UI components
├─────────────────────────────────────────────┤
│            Composition Layer                │ ← Layout & structure
├─────────────────────────────────────────────┤
│             Business Layer                  │ ← Logic & state
├─────────────────────────────────────────────┤
│              Data Layer                     │ ← Hooks & services
└─────────────────────────────────────────────┘
```

## 🏗️ **Core Composition Patterns**

### **Pattern 1: Compound Components with Context**

**Problem**: Complex UI components with multiple related parts need to share state and behavior.

**Solution**: Compound components using React Context for internal communication.

```typescript
// src/components/MessageActions/MessageActions.tsx
interface MessageActionsContextValue {
  selectedMessages: Set<string>
  isProcessing: boolean
  processingProgress: number
  selectMessage: (id: string) => void
  deselectMessage: (id: string) => void
  executeAction: (action: string) => Promise<void>
}

const MessageActionsContext = React.createContext<MessageActionsContextValue | null>(null)

const useMessageActionsContext = () => {
  const context = useContext(MessageActionsContext)
  if (!context) {
    throw new Error('MessageActions compound components must be used within MessageActions.Provider')
  }
  return context
}

// Main compound component
export interface MessageActionsProps {
  children: React.ReactNode
  messages: StoredMessage[]
  onActionComplete?: (action: string, messageIds: string[]) => void
}

export const MessageActions: React.FC<MessageActionsProps> & {
  Toolbar: typeof MessageActionsToolbar
  SelectionInfo: typeof MessageActionsSelectionInfo
  ActionButton: typeof MessageActionButton
  ProgressBar: typeof MessageActionsProgressBar
} = ({ children, messages, onActionComplete }) => {
  const {
    state,
    selectMessage,
    deselectMessage,
    executeAction,
  } = useMessageActions()

  const contextValue: MessageActionsContextValue = {
    selectedMessages: state.selectedMessages,
    isProcessing: state.isProcessing,
    processingProgress: state.processingProgress,
    selectMessage,
    deselectMessage,
    executeAction: async (action: string) => {
      try {
        await executeAction(action, Array.from(state.selectedMessages))
        onActionComplete?.(action, Array.from(state.selectedMessages))
      } catch (error) {
        console.error(`Failed to execute action ${action}:`, error)
      }
    },
  }

  return (
    <MessageActionsContext.Provider value={contextValue}>
      <div className="message-actions-container">
        {children}
      </div>
    </MessageActionsContext.Provider>
  )
}

// Toolbar sub-component
const MessageActionsToolbar: React.FC<{
  children: React.ReactNode
  className?: string
}> = ({ children, className = '' }) => {
  const { selectedMessages, isProcessing } = useMessageActionsContext()
  
  if (selectedMessages.size === 0) return null

  return (
    <div className={`message-actions-toolbar bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-blue-800">
            {selectedMessages.size} message{selectedMessages.size !== 1 ? 's' : ''} selected
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {children}
        </div>
      </div>
    </div>
  )
}

// Selection info sub-component
const MessageActionsSelectionInfo: React.FC<{
  showDetails?: boolean
  className?: string
}> = ({ showDetails = false, className = '' }) => {
  const { selectedMessages } = useMessageActionsContext()

  return (
    <div className={`selection-info ${className}`}>
      <span className="text-sm text-gray-600">
        {selectedMessages.size} selected
      </span>
      
      {showDetails && selectedMessages.size > 0 && (
        <div className="mt-1 text-xs text-gray-500">
          IDs: {Array.from(selectedMessages).slice(0, 3).join(', ')}
          {selectedMessages.size > 3 && ` +${selectedMessages.size - 3} more`}
        </div>
      )}
    </div>
  )
}

// Action button sub-component
const MessageActionButton: React.FC<{
  action: 'copy' | 'delete' | 'export' | 'regenerate'
  icon: React.ReactNode
  children: React.ReactNode
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'danger'
  className?: string
}> = ({ 
  action, 
  icon, 
  children, 
  disabled = false, 
  variant = 'secondary',
  className = '' 
}) => {
  const { selectedMessages, isProcessing, executeAction } = useMessageActionsContext()

  const handleClick = async () => {
    if (selectedMessages.size === 0 || isProcessing) return
    await executeAction(action)
  }

  const variantStyles = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }

  const isDisabled = disabled || selectedMessages.size === 0 || isProcessing

  return (
    <button
      onClick={handleClick}
      disabled={isDisabled}
      className={`
        flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition-colors
        ${variantStyles[variant]}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      {icon}
      {children}
      {isProcessing && action === 'processing' && (
        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
      )}
    </button>
  )
}

// Progress bar sub-component  
const MessageActionsProgressBar: React.FC<{
  className?: string
}> = ({ className = '' }) => {
  const { isProcessing, processingProgress } = useMessageActionsContext()

  if (!isProcessing) return null

  return (
    <div className={`progress-bar-container ${className}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-600">Processing...</span>
        <span className="text-xs text-gray-600">{Math.round(processingProgress)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${processingProgress}%` }}
        />
      </div>
    </div>
  )
}

// Attach sub-components to main component
MessageActions.Toolbar = MessageActionsToolbar
MessageActions.SelectionInfo = MessageActionsSelectionInfo
MessageActions.ActionButton = MessageActionButton
MessageActions.ProgressBar = MessageActionsProgressBar

// Usage example
export const MessageActionsExample: React.FC = () => {
  return (
    <MessageActions messages={messages} onActionComplete={handleActionComplete}>
      <MessageActions.Toolbar>
        <MessageActions.ActionButton
          action="copy"
          icon={<Copy className="w-4 h-4" />}
          variant="secondary"
        >
          Copy
        </MessageActions.ActionButton>
        
        <MessageActions.ActionButton
          action="delete"
          icon={<Trash className="w-4 h-4" />}
          variant="danger"
        >
          Delete
        </MessageActions.ActionButton>
        
        <MessageActions.SelectionInfo showDetails />
      </MessageActions.Toolbar>
      
      <MessageActions.ProgressBar />
    </MessageActions>
  )
}
```

**Key Benefits**:
- **Flexible composition**: Mix and match sub-components as needed
- **Shared state**: Context eliminates prop drilling
- **Type safety**: TypeScript ensures proper usage
- **Discoverability**: Attached sub-components are easily found

### **Pattern 2: Polymorphic Components with Generics**

**Problem**: Components need to work with different HTML elements or component types while maintaining type safety.

**Solution**: Polymorphic components using TypeScript generics and `as` prop.

```typescript
// src/components/Button/Button.tsx
type AsProp<C extends React.ElementType> = {
  as?: C
}

type PropsToOmit<C extends React.ElementType, P> = keyof (AsProp<C> & P)

// This gives us nice IntelliSense for all valid HTML attributes
type PolymorphicComponentProp<C extends React.ElementType, Props = {}> = 
  React.PropsWithChildren<Props & AsProp<C>> &
  Omit<React.ComponentPropsWithoutRef<C>, PropsToOmit<C, Props>>

type PolymorphicRef<C extends React.ElementType> = React.ComponentPropsWithRef<C>['ref']

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

export type ButtonComponent = <C extends React.ElementType = 'button'>(
  props: PolymorphicComponentProp<C, ButtonProps> & { ref?: PolymorphicRef<C> }
) => React.ReactElement | null

export const Button: ButtonComponent = React.forwardRef(
  <C extends React.ElementType = 'button'>(
    {
      as,
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      children,
      className,
      ...restProps
    }: PolymorphicComponentProp<C, ButtonProps>,
    ref?: PolymorphicRef<C>
  ) => {
    const Component = as || 'button'

    const variantStyles = {
      primary: 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700 focus:ring-blue-500',
      secondary: 'bg-gray-600 text-white border-gray-600 hover:bg-gray-700 focus:ring-gray-500',
      outline: 'bg-transparent text-blue-600 border-blue-600 hover:bg-blue-50 focus:ring-blue-500',
      ghost: 'bg-transparent text-gray-600 border-transparent hover:bg-gray-100 focus:ring-gray-500',
      danger: 'bg-red-600 text-white border-red-600 hover:bg-red-700 focus:ring-red-500',
    }

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm', 
      lg: 'px-6 py-3 text-base',
    }

    const baseStyles = `
      inline-flex items-center justify-center gap-2 font-medium rounded-lg border
      transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      ${fullWidth ? 'w-full' : ''}
      ${variantStyles[variant]}
      ${sizeStyles[size]}
    `

    const buttonProps = {
      ref,
      className: `${baseStyles} ${className || ''}`,
      disabled: disabled || loading,
      'aria-busy': loading,
      ...restProps,
    }

    return (
      <Component {...buttonProps}>
        {loading && (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        )}
        {!loading && leftIcon && leftIcon}
        {children}
        {!loading && rightIcon && rightIcon}
      </Component>
    )
  }
) as ButtonComponent

// Usage examples with full type safety
export const ButtonExamples: React.FC = () => {
  return (
    <div className="space-y-4">
      {/* Standard button */}
      <Button onClick={() => console.log('clicked')}>
        Click me
      </Button>

      {/* Button as link - gets full anchor props with IntelliSense */}
      <Button as="a" href="/dashboard" target="_blank">
        Go to Dashboard
      </Button>

      {/* Button as React Router Link */}
      <Button as={Link} to="/conversations">
        View Conversations  
      </Button>

      {/* Button with icons */}
      <Button
        leftIcon={<Plus className="w-4 h-4" />}
        variant="primary"
      >
        New Conversation
      </Button>

      {/* Loading state */}
      <Button loading disabled>
        Saving...
      </Button>
    </div>
  )
}
```

**Key Benefits**:
- **Full type safety**: IntelliSense for all valid props based on `as` prop
- **Flexible rendering**: Same component, different HTML elements
- **Consistent styling**: Unified appearance across different elements
- **Framework agnostic**: Works with any routing library

### **Pattern 3: Render Prop Components with Hooks**

**Problem**: Components need to share complex logic but render differently based on context.

**Solution**: Render prop pattern combined with custom hooks for logic reuse.

```typescript
// src/components/ConversationList/ConversationList.tsx
interface ConversationListRenderProps {
  conversations: StoredConversation[]
  isLoading: boolean
  error: Error | null
  selectedConversation: string | null
  searchQuery: string
  filters: ConversationFilters
  
  // Actions
  selectConversation: (id: string) => void
  setSearchQuery: (query: string) => void
  setFilters: (filters: Partial<ConversationFilters>) => void
  refreshConversations: () => void
  createConversation: (title: string) => Promise<string>
  archiveConversation: (id: string) => Promise<void>
}

export interface ConversationListProps {
  children: (props: ConversationListRenderProps) => React.ReactNode
  initialFilters?: Partial<ConversationFilters>
  autoSelectFirst?: boolean
  onConversationSelect?: (conversation: StoredConversation) => void
}

export const ConversationList: React.FC<ConversationListProps> = ({
  children,
  initialFilters = {},
  autoSelectFirst = false,
  onConversationSelect,
}) => {
  // Use custom hook for all the logic
  const conversationState = useConversationList({
    initialFilters,
    autoSelectFirst,
    onConversationSelect,
  })

  // Pass everything to the render prop
  return <>{children(conversationState)}</>
}

// Custom hook that contains all the logic
export const useConversationList = ({
  initialFilters = {},
  autoSelectFirst = false,
  onConversationSelect,
}: {
  initialFilters?: Partial<ConversationFilters>
  autoSelectFirst?: boolean
  onConversationSelect?: (conversation: StoredConversation) => void
}) => {
  const [conversations, setConversations] = useState<StoredConversation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<ConversationFilters>({
    folder: null,
    starred: null,
    archived: false,
    tags: [],
    dateRange: null,
    ...initialFilters,
  })

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        const loaded = await messageStorage.loadConversations({
          limit: 100,
          ...filters,
        })
        setConversations(loaded)
        
        // Auto-select first conversation if requested
        if (autoSelectFirst && loaded.length > 0 && !selectedConversation) {
          const firstConv = loaded[0]
          setSelectedConversation(firstConv.id)
          onConversationSelect?.(firstConv)
        }
      } catch (err) {
        setError(err as Error)
      } finally {
        setIsLoading(false)
      }
    }

    loadConversations()
  }, [filters, autoSelectFirst, selectedConversation, onConversationSelect])

  // Filter conversations based on search query
  const filteredConversations = useMemo(() => {
    if (!searchQuery) return conversations
    
    const query = searchQuery.toLowerCase()
    return conversations.filter(conv =>
      conv.title.toLowerCase().includes(query) ||
      conv.description?.toLowerCase().includes(query) ||
      conv.tags.some(tag => tag.toLowerCase().includes(query))
    )
  }, [conversations, searchQuery])

  const selectConversation = useCallback((id: string) => {
    const conversation = conversations.find(c => c.id === id)
    if (conversation) {
      setSelectedConversation(id)
      onConversationSelect?.(conversation)
    }
  }, [conversations, onConversationSelect])

  const updateFilters = useCallback((newFilters: Partial<ConversationFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  const refreshConversations = useCallback(() => {
    // Trigger reload by updating a dependency
    setFilters(prev => ({ ...prev }))
  }, [])

  const createConversation = useCallback(async (title: string): Promise<string> => {
    try {
      const conversationId = await messageStorage.createConversation(title)
      refreshConversations()
      return conversationId
    } catch (err) {
      setError(err as Error)
      throw err
    }
  }, [refreshConversations])

  const archiveConversation = useCallback(async (id: string): Promise<void> => {
    try {
      const conversation = conversations.find(c => c.id === id)
      if (conversation) {
        await messageStorage.saveConversation({
          ...conversation,
          archived: true,
        })
        refreshConversations()
      }
    } catch (err) {
      setError(err as Error)
      throw err
    }
  }, [conversations, refreshConversations])

  return {
    conversations: filteredConversations,
    isLoading,
    error,
    selectedConversation,
    searchQuery,
    filters,
    selectConversation,
    setSearchQuery,
    setFilters: updateFilters,
    refreshConversations,
    createConversation,
    archiveConversation,
  }
}

// Different UI implementations using the same logic
export const ConversationListExamples: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Simple list view */}
      <ConversationList>
        {({ conversations, isLoading, selectConversation, selectedConversation }) => (
          <div className="simple-list">
            {isLoading ? (
              <div>Loading...</div>
            ) : (
              conversations.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`block w-full p-3 text-left border rounded ${
                    selectedConversation === conv.id ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
                  }`}
                >
                  <div className="font-medium">{conv.title}</div>
                  <div className="text-sm text-gray-500">
                    {conv.messageCount} messages • {formatRelativeTime(conv.lastActivity)}
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </ConversationList>

      {/* Card grid view */}
      <ConversationList>
        {({ conversations, isLoading, selectConversation, searchQuery, setSearchQuery }) => (
          <div className="card-grid">
            <div className="mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            
            {isLoading ? (
              <div>Loading...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {conversations.map(conv => (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className="p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-blue-300 hover:shadow-sm"
                  >
                    <h3 className="font-medium mb-2">{conv.title}</h3>
                    <div className="text-sm text-gray-500 mb-2">
                      {conv.description || 'No description'}
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>{conv.messageCount} messages</span>
                      <span>{formatRelativeTime(conv.lastActivity)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </ConversationList>

      {/* Advanced table view */}
      <ConversationList>
        {({ 
          conversations, 
          isLoading, 
          error, 
          selectConversation, 
          archiveConversation,
          filters,
          setFilters,
        }) => (
          <div className="advanced-table">
            {/* Filters */}
            <div className="mb-4 flex gap-4">
              <select
                value={filters.folder || ''}
                onChange={(e) => setFilters({ folder: e.target.value || null })}
                className="p-2 border border-gray-300 rounded"
              >
                <option value="">All folders</option>
                <option value="work">Work</option>
                <option value="personal">Personal</option>
              </select>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.starred || false}
                  onChange={(e) => setFilters({ starred: e.target.checked })}
                />
                Starred only
              </label>
            </div>

            {/* Error state */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
                Error: {error.message}
              </div>
            )}

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full border border-gray-200 rounded">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-3 text-left">Title</th>
                    <th className="p-3 text-left">Messages</th>
                    <th className="p-3 text-left">Last Activity</th>
                    <th className="p-3 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {conversations.map(conv => (
                    <tr key={conv.id} className="border-t border-gray-200 hover:bg-gray-50">
                      <td 
                        className="p-3 cursor-pointer"
                        onClick={() => selectConversation(conv.id)}
                      >
                        <div className="font-medium">{conv.title}</div>
                        {conv.description && (
                          <div className="text-sm text-gray-500">{conv.description}</div>
                        )}
                      </td>
                      <td className="p-3">{conv.messageCount}</td>
                      <td className="p-3">{formatRelativeTime(conv.lastActivity)}</td>
                      <td className="p-3">
                        <button
                          onClick={() => archiveConversation(conv.id)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Archive
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ConversationList>
    </div>
  )
}
```

**Key Benefits**:
- **Logic reuse**: Same hook can power different UIs
- **Flexible rendering**: Complete control over presentation
- **Separation of concerns**: Logic separated from presentation
- **Easy testing**: Hook can be tested independently

### **Pattern 4: Higher-Order Components for Cross-Cutting Concerns**

**Problem**: Multiple components need the same cross-cutting functionality (authentication, error boundaries, analytics).

**Solution**: Higher-order components that wrap functionality around existing components.

```typescript
// src/components/hoc/withErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
  errorId: string
}

interface WithErrorBoundaryOptions {
  fallback?: React.ComponentType<{ 
    error: Error
    errorInfo: React.ErrorInfo
    retry: () => void 
  }>
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
  isolate?: boolean // Whether errors should be isolated to this component
  retryable?: boolean
}

export function withErrorBoundary<P extends {}>(
  WrappedComponent: React.ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
): React.ComponentType<P> {
  const {
    fallback: FallbackComponent,
    onError,
    isolate = true,
    retryable = true,
  } = options

  class ErrorBoundaryWrapper extends React.Component<P, ErrorBoundaryState> {
    private retryCount = 0
    private readonly maxRetries = 3

    constructor(props: P) {
      super(props)
      
      this.state = {
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
      }
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
      return {
        hasError: true,
        error,
        errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      this.setState({ errorInfo })

      // Custom error handler
      onError?.(error, errorInfo)

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group(`🚨 Error Boundary: ${WrappedComponent.displayName || WrappedComponent.name}`)
        console.error('Error:', error)
        console.error('Error Info:', errorInfo)
        console.error('Component Stack:', errorInfo.componentStack)
        console.groupEnd()
      }

      // Report to error tracking service in production
      if (process.env.NODE_ENV === 'production') {
        this.reportError(error, errorInfo)
      }
    }

    private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
      // Example error reporting
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        component: WrappedComponent.displayName || WrappedComponent.name,
        errorId: this.state.errorId,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        retryCount: this.retryCount,
      }

      // Send to error tracking service
      console.log('Would report error:', errorReport)
    }

    private handleRetry = () => {
      if (this.retryCount < this.maxRetries) {
        this.retryCount++
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          errorId: '',
        })
      }
    }

    render() {
      if (this.state.hasError && this.state.error && this.state.errorInfo) {
        // Use custom fallback if provided
        if (FallbackComponent) {
          return (
            <FallbackComponent
              error={this.state.error}
              errorInfo={this.state.errorInfo}
              retry={this.handleRetry}
            />
          )
        }

        // Default error UI
        const canRetry = retryable && this.retryCount < this.maxRetries

        return (
          <div className="error-boundary-fallback bg-red-50 border border-red-200 rounded-lg p-4 m-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <h3 className="text-lg font-medium text-red-800">
                Something went wrong
              </h3>
            </div>

            <p className="text-red-700 mb-4">
              The component "{WrappedComponent.displayName || WrappedComponent.name}" 
              encountered an error and couldn't render properly.
            </p>

            <div className="flex gap-3 mb-4">
              {canRetry && (
                <button
                  onClick={this.handleRetry}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Try Again ({this.maxRetries - this.retryCount} attempts left)
                </button>
              )}
              
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Reload Page
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-red-700 mb-2">
                  Error Details (Development)
                </summary>
                <div className="bg-red-100 p-3 rounded overflow-auto">
                  <div className="mb-2">
                    <strong>Error:</strong> {this.state.error.message}
                  </div>
                  <div className="mb-2">
                    <strong>Stack:</strong>
                    <pre className="text-xs mt-1">{this.state.error.stack}</pre>
                  </div>
                  <div>
                    <strong>Component Stack:</strong>
                    <pre className="text-xs mt-1">{this.state.errorInfo.componentStack}</pre>
                  </div>
                </div>
              </details>
            )}
          </div>
        )
      }

      return <WrappedComponent {...this.props} />
    }
  }

  // Set display name for debugging
  ErrorBoundaryWrapper.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`

  return ErrorBoundaryWrapper
}

// HOC for analytics tracking
export function withAnalytics<P extends {}>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    trackMount?: boolean
    trackUnmount?: boolean
    trackProps?: boolean
    eventName?: string
  } = {}
): React.ComponentType<P> {
  const {
    trackMount = true,
    trackUnmount = false,
    trackProps = false,
    eventName,
  } = options

  const AnalyticsWrapper: React.FC<P> = (props) => {
    const componentName = WrappedComponent.displayName || WrappedComponent.name
    const mountTime = useRef<Date>()

    useEffect(() => {
      mountTime.current = new Date()
      
      if (trackMount) {
        // Track component mount
        console.log(`📊 Component mounted: ${componentName}`, {
          eventName: eventName || `${componentName}_mount`,
          timestamp: mountTime.current.toISOString(),
          props: trackProps ? props : undefined,
        })
      }

      return () => {
        if (trackUnmount && mountTime.current) {
          const duration = Date.now() - mountTime.current.getTime()
          console.log(`📊 Component unmounted: ${componentName}`, {
            eventName: eventName || `${componentName}_unmount`,
            duration,
            timestamp: new Date().toISOString(),
          })
        }
      }
    }, [componentName, props])

    return <WrappedComponent {...props} />
  }

  AnalyticsWrapper.displayName = `withAnalytics(${componentName})`
  
  return AnalyticsWrapper
}

// HOC for loading states
export function withLoading<P extends {}>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    LoadingComponent?: React.ComponentType
    loadingProp?: keyof P
    minimumLoadingTime?: number
  } = {}
): React.ComponentType<P> {
  const {
    LoadingComponent = DefaultLoadingComponent,
    loadingProp = 'isLoading' as keyof P,
    minimumLoadingTime = 300,
  } = options

  const LoadingWrapper: React.FC<P> = (props) => {
    const [showLoading, setShowLoading] = useState(false)
    const [minTimeElapsed, setMinTimeElapsed] = useState(false)
    const isLoading = props[loadingProp] as boolean

    // Handle minimum loading time
    useEffect(() => {
      if (isLoading && !showLoading) {
        setShowLoading(true)
        setMinTimeElapsed(false)
        
        const timer = setTimeout(() => {
          setMinTimeElapsed(true)
        }, minimumLoadingTime)

        return () => clearTimeout(timer)
      }
    }, [isLoading, showLoading, minimumLoadingTime])

    useEffect(() => {
      if (!isLoading && minTimeElapsed) {
        setShowLoading(false)
      }
    }, [isLoading, minTimeElapsed])

    if (showLoading) {
      return <LoadingComponent />
    }

    return <WrappedComponent {...props} />
  }

  LoadingWrapper.displayName = `withLoading(${WrappedComponent.displayName || WrappedComponent.name})`
  
  return LoadingWrapper
}

const DefaultLoadingComponent: React.FC = () => (
  <div className="flex items-center justify-center p-8">
    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
  </div>
)

// Usage examples
const SafeMessageComponent = withErrorBoundary(
  withAnalytics(
    withLoading(MessageComponent, {
      loadingProp: 'isLoading',
      minimumLoadingTime: 500,
    }),
    {
      trackMount: true,
      eventName: 'message_component_view',
    }
  ),
  {
    retryable: true,
    onError: (error, errorInfo) => {
      console.error('Message component error:', error)
    }
  }
)
```

**Key Benefits**:
- **Cross-cutting concerns**: Handle common functionality consistently
- **Composable**: HOCs can be stacked and combined
- **Reusable**: Same HOC works with any component
- **Isolated**: Each concern is handled separately

## 🎯 **Component Testing Patterns**

### **Testing Compound Components**

```typescript
// src/components/MessageActions/__tests__/MessageActions.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MessageActions } from '../MessageActions'

const mockMessages = [
  { id: 'msg-1', content: 'Test message 1', role: 'user' as const },
  { id: 'msg-2', content: 'Test message 2', role: 'assistant' as const },
]

describe('MessageActions Compound Component', () => {
  it('should render toolbar when messages are selected', () => {
    render(
      <MessageActions messages={mockMessages}>
        <MessageActions.Toolbar>
          <MessageActions.ActionButton
            action="copy"
            icon={<span>📋</span>}
          >
            Copy
          </MessageActions.ActionButton>
        </MessageActions.Toolbar>
      </MessageActions>
    )

    // Toolbar should not be visible initially (no messages selected)
    expect(screen.queryByRole('button', { name: /copy/i })).not.toBeInTheDocument()
    
    // Select a message through the internal API (would be done by message components in real usage)
    // This test would need to be more integrated or use a test helper
  })

  it('should handle action execution correctly', async () => {
    const onActionComplete = jest.fn()
    
    render(
      <MessageActions messages={mockMessages} onActionComplete={onActionComplete}>
        <MessageActions.Toolbar>
          <MessageActions.ActionButton
            action="copy"
            icon={<span>📋</span>}
          >
            Copy
          </MessageActions.ActionButton>
        </MessageActions.Toolbar>
      </MessageActions>
    )

    // Integration test would involve selecting messages and executing actions
    // This demonstrates the pattern for testing compound components
  })

  it('should show progress during action execution', async () => {
    render(
      <MessageActions messages={mockMessages}>
        <MessageActions.ProgressBar />
      </MessageActions>
    )

    // Test progress bar functionality
    // Would need to trigger an action and verify progress is shown
  })
})
```

### **Testing Polymorphic Components**

```typescript
// src/components/Button/__tests__/Button.test.tsx
import { render, screen } from '@testing-library/react'
import { Button } from '../Button'

describe('Button Polymorphic Component', () => {
  it('should render as button by default', () => {
    render(<Button>Click me</Button>)
    
    const element = screen.getByRole('button', { name: /click me/i })
    expect(element.tagName).toBe('BUTTON')
  })

  it('should render as anchor when as="a"', () => {
    render(
      <Button as="a" href="https://example.com">
        Visit site
      </Button>
    )
    
    const element = screen.getByRole('link', { name: /visit site/i })
    expect(element.tagName).toBe('A')
    expect(element).toHaveAttribute('href', 'https://example.com')
  })

  it('should apply variant styles correctly', () => {
    render(<Button variant="danger">Delete</Button>)
    
    const button = screen.getByRole('button', { name: /delete/i })
    expect(button).toHaveClass('bg-red-600')
  })

  it('should handle loading state', () => {
    render(<Button loading>Loading</Button>)
    
    const button = screen.getByRole('button', { name: /loading/i })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(button.querySelector('.animate-spin')).toBeInTheDocument()
  })
})
```

## 🎯 **Performance Optimization Patterns**

### **Memoization in Composed Components**

```typescript
// src/components/OptimizedMessageList.tsx
interface MessageListProps {
  messages: StoredMessage[]
  onMessageSelect: (id: string) => void
  selectedMessages: Set<string>
  renderMessage?: (message: StoredMessage, index: number) => React.ReactNode
}

export const OptimizedMessageList: React.FC<MessageListProps> = ({
  messages,
  onMessageSelect,
  selectedMessages,
  renderMessage,
}) => {
  // Memoize the default message renderer
  const defaultRenderMessage = useCallback(
    (message: StoredMessage, index: number) => (
      <MessageItem
        key={message.id}
        message={message}
        isSelected={selectedMessages.has(message.id)}
        onSelect={onMessageSelect}
      />
    ),
    [selectedMessages, onMessageSelect]
  )

  // Use provided renderer or default
  const messageRenderer = renderMessage || defaultRenderMessage

  // Memoize the rendered messages list
  const renderedMessages = useMemo(() => {
    return messages.map(messageRenderer)
  }, [messages, messageRenderer])

  return (
    <div className="message-list">
      {renderedMessages}
    </div>
  )
}

// Memoized message item component
const MessageItem = memo<{
  message: StoredMessage
  isSelected: boolean
  onSelect: (id: string) => void
}>(({ message, isSelected, onSelect }) => {
  const handleSelect = useCallback(() => {
    onSelect(message.id)
  }, [message.id, onSelect])

  return (
    <div
      onClick={handleSelect}
      className={`message-item p-3 border rounded ${
        isSelected ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
      }`}
    >
      <div className="message-content">
        {message.content}
      </div>
      <div className="message-meta text-xs text-gray-500">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
    </div>
  )
})
```

## 🎯 **Key Architectural Decisions**

### **Component Composition Hierarchy**

```
MessageActionsProvider (Context + Logic)
├── MessageActionsToolbar (Layout + Controls)
│   ├── MessageActionButton (Individual Actions)
│   ├── MessageSelectionInfo (Status Display)
│   └── MessageActionsProgressBar (Progress Feedback)
├── MessageList (Data Display)
│   └── MessageItem (Individual Items)
└── MessageActionsContext (State Sharing)
```

### **When to Use Each Pattern**

| Pattern | Use Case | Benefits | Trade-offs |
|---------|----------|----------|------------|
| **Compound Components** | Complex UI with multiple related parts | Flexible composition, shared state | More complex API |
| **Polymorphic Components** | Components that need different HTML elements | Type safety, flexibility | Complex TypeScript |
| **Render Props** | Logic reuse with different UIs | Maximum flexibility | More verbose |
| **HOCs** | Cross-cutting concerns | Composable, reusable | Can create wrapper hell |

### **Performance Guidelines**

- **Memoize expensive computations**: Use `useMemo` for derived state
- **Optimize callback functions**: Use `useCallback` to prevent re-renders
- **Implement React.memo**: For pure components that re-render often
- **Split complex components**: Separate logic from presentation
- **Use context judiciously**: Don't overuse context for local state

## 🎯 **Key Takeaways**

1. **Favor composition over inheritance** - Build flexible, reusable components
2. **Separate logic from presentation** - Use hooks for logic, components for UI
3. **Type your compositions** - TypeScript ensures proper usage patterns
4. **Test each pattern appropriately** - Different patterns need different test strategies
5. **Optimize selectively** - Profile before optimizing complex compositions
6. **Document your patterns** - Clear APIs help team adoption
7. **Keep it simple** - Don't over-engineer for flexibility you don't need

---

**Next**: [04-performance-optimization-strategies.md](./04-performance-optimization-strategies.md) - Production Performance Patterns

**Previous**: [02-state-management-patterns.md](./02-state-management-patterns.md)