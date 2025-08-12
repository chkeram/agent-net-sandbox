# Example 3: RoutingReasoning Component - Expandable AI Decision Display

## 🎯 **What You'll Learn**

This tutorial provides a **complete breakdown** of the `RoutingReasoning.tsx` component from our production frontend. You'll understand:
- **Expandable UI patterns** for showing/hiding complex information
- **Confidence score visualization** with dynamic colors and badges
- **Multi-step reasoning displays** with visual step indicators
- **Animation and interaction patterns** for professional UX
- **Data parsing strategies** for AI routing decisions

## 🏗️ **Component Overview**

The `RoutingReasoning` component is responsible for displaying AI routing transparency in our chat interface. It shows:
- **Which agent was selected** and why
- **Confidence scores** with visual indicators
- **Step-by-step AI reasoning** process
- **Alternative agents** that were considered
- **Processing time** and metadata

## 📋 **Component Architecture**

### **Core Interface**

```typescript
interface RoutingReasoningProps {
  agentInfo: {
    id: string
    name: string
    protocol: string
    confidence: number
  }
  reasoning?: string
  processingTime: number
  showByDefault?: boolean
  className?: string
}
```

## 🔍 **Complete Component Breakdown**

Let's analyze the real production code section by section:

### **Step 1: Component State Management**

```typescript
export const RoutingReasoning: React.FC<RoutingReasoningProps> = ({
  agentInfo,
  reasoning,
  processingTime,
  showByDefault = false,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(showByDefault)
  
  // Parse reasoning text into structured data
  const reasoningSteps = useMemo(() => {
    if (!reasoning) return []
    
    try {
      // Try to parse as JSON first (structured reasoning)
      const parsed = JSON.parse(reasoning)
      return Array.isArray(parsed) ? parsed : [parsed]
    } catch {
      // Fall back to text parsing
      return parseTextReasoning(reasoning)
    }
  }, [reasoning])
```

**Key Patterns:**
- **Controlled expansion state** with `useState`
- **Lazy parsing** with `useMemo` to avoid re-parsing on every render
- **Graceful fallback** from JSON to text parsing
- **Props destructuring** with defaults for clean API

### **Step 2: Dynamic Confidence Visualization**

```typescript
const getConfidenceColor = useCallback((confidence: number) => {
  if (confidence >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
  if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  return 'text-red-600 bg-red-50 border-red-200'
}, [])

const getConfidenceIcon = useCallback((confidence: number) => {
  if (confidence >= 0.8) return <CheckCircle className="w-4 h-4" />
  if (confidence >= 0.6) return <AlertTriangle className="w-4 h-4" />
  return <XCircle className="w-4 h-4" />
}, [])
```

**Key Patterns:**
- **useCallback optimization** for functions used in render
- **Threshold-based styling** with semantic colors
- **Consistent visual language** across confidence levels
- **Icon + color combinations** for accessibility

### **Step 3: Expandable Header Design**

```typescript
return (
  <div className={`routing-reasoning bg-blue-50 border border-blue-200 rounded-lg overflow-hidden transition-all duration-200 ${className}`}>
    {/* Always-visible header */}
    <div 
      className="flex items-center justify-between p-3 cursor-pointer hover:bg-blue-100 transition-colors"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">
            AI Routing Decision
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">
            Selected: <span className="font-medium">{agentInfo.name}</span>
          </span>
          <span className="text-xs text-gray-500">
            ({agentInfo.protocol.toUpperCase()})
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Confidence badge */}
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full border ${getConfidenceColor(agentInfo.confidence)}`}>
          {getConfidenceIcon(agentInfo.confidence)}
          <span className="text-xs font-semibold">
            {Math.round(agentInfo.confidence * 100)}%
          </span>
        </div>
        
        {/* Expand/collapse icon */}
        <div className="transition-transform duration-200" style={{
          transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)'
        }}>
          <ChevronDown className="w-4 h-4 text-blue-600" />
        </div>
      </div>
    </div>
```

**Key Patterns:**
- **Hover states** with `hover:bg-blue-100` for interactivity feedback
- **Smooth transitions** with `transition-all duration-200`
- **Inline transform styles** for rotation animation
- **Information hierarchy** with font weights and colors
- **Semantic spacing** with Tailwind gap utilities

### **Step 4: Expandable Content with Animation**

```typescript
    {/* Expandable content */}
    <div className={`transition-all duration-300 ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
      <div className="border-t border-blue-200 p-4 bg-white">
        {reasoningSteps.length > 0 ? (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              AI Reasoning Steps
            </h4>
            
            <div className="space-y-2">
              {reasoningSteps.map((step, index) => (
                <ReasoningStep key={index} step={step} index={index} />
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No detailed reasoning available</p>
          </div>
        )}
        
        {/* Processing metadata */}
        <div className="mt-4 pt-3 border-t border-gray-200 flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {processingTime}ms
            </span>
            <span className="flex items-center gap-1">
              <Target className="w-3 h-3" />
              {agentInfo.protocol.toUpperCase()} Protocol
            </span>
          </div>
          <span>Agent ID: {agentInfo.id.slice(-8)}</span>
        </div>
      </div>
    </div>
  </div>
)
```

**Key Patterns:**
- **Max-height animation** for smooth expand/collapse
- **Combined opacity + height** transitions for polished feel
- **Conditional rendering** with meaningful empty states
- **Metadata footer** with processing details
- **Consistent iconography** throughout component

### **Step 5: ReasoningStep Sub-Component**

```typescript
const ReasoningStep: React.FC<{ 
  step: any
  index: number 
}> = ({ step, index }) => {
  const [isStepExpanded, setIsStepExpanded] = useState(false)
  
  return (
    <div className="reasoning-step bg-gray-50 rounded-lg p-3 border border-gray-200">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsStepExpanded(!isStepExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-800 rounded-full text-xs font-bold">
            {index + 1}
          </div>
          <span className="text-sm font-medium text-gray-800">
            {step.description || `Reasoning Step ${index + 1}`}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {step.confidence && (
            <span className="text-xs text-gray-500">
              {Math.round(step.confidence * 100)}%
            </span>
          )}
          <ChevronRight className={`w-3 h-3 text-gray-400 transition-transform ${
            isStepExpanded ? 'rotate-90' : 'rotate-0'
          }`} />
        </div>
      </div>
      
      {isStepExpanded && step.details && (
        <div className="mt-3 pt-3 border-t border-gray-300">
          <p className="text-sm text-gray-700">{step.details}</p>
          {step.factors && step.factors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {step.factors.map((factor: string, i: number) => (
                <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                  {factor}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

**Key Patterns:**
- **Nested expansion** - steps can expand independently  
- **Step numbering** with circular indicators
- **Factor tags** for additional context
- **Progressive disclosure** - details shown on demand

## 🎨 **Advanced Styling Patterns**

### **1. Confidence-Based Theming**

```typescript
// Dynamic theme based on confidence score
const theme = useMemo(() => {
  const confidence = agentInfo.confidence
  
  if (confidence >= 0.8) return {
    bg: 'bg-green-50',
    border: 'border-green-200', 
    text: 'text-green-800',
    accent: 'text-green-600'
  }
  
  if (confidence >= 0.6) return {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-800', 
    accent: 'text-yellow-600'
  }
  
  return {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-800',
    accent: 'text-red-600'
  }
}, [agentInfo.confidence])
```

### **2. Animation Timing**

```css
/* Custom timing for complex animations */
.routing-reasoning {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.routing-reasoning .expandable-content {
  transition: max-height 0.3s ease-out, opacity 0.2s ease-out;
}

.routing-reasoning .step-indicator {
  transition: transform 0.15s ease-in-out;
}
```

## 🔄 **Data Flow Patterns**

### **Reasoning Text Parsing**

```typescript
const parseTextReasoning = (reasoning: string) => {
  // Split reasoning into logical steps
  const sentences = reasoning.split(/[.!?]+/).filter(s => s.trim().length > 10)
  
  return sentences.map((sentence, index) => ({
    description: sentence.trim(),
    details: '',
    confidence: 0.8, // Default confidence
    factors: extractFactors(sentence)
  }))
}

const extractFactors = (text: string) => {
  // Extract key factors from reasoning text
  const factors = []
  
  if (text.includes('math') || text.includes('calculation')) {
    factors.push('Mathematical Capability')
  }
  if (text.includes('fast') || text.includes('quick')) {
    factors.push('Response Speed')  
  }
  if (text.includes('accurate') || text.includes('precise')) {
    factors.push('Accuracy')
  }
  
  return factors
}
```

## 🎯 **Usage Examples**

### **Basic Usage**

```typescript
// In StreamingChatContainer.tsx
<RoutingReasoning
  agentInfo={{
    id: 'a2a-math',
    name: 'Math Agent',
    protocol: 'a2a',
    confidence: 0.95
  }}
  reasoning="The query requires mathematical computation. The A2A Math Agent specializes in arithmetic operations and is currently available with excellent performance metrics."
  processingTime={1250}
  showByDefault={false}
/>
```

### **With Structured Reasoning**

```typescript
const structuredReasoning = JSON.stringify([
  {
    description: "Query Analysis",
    details: "Identified mathematical intent with high confidence",
    confidence: 0.92,
    factors: ["Math Keywords", "Calculation Pattern"]
  },
  {
    description: "Agent Matching", 
    details: "A2A Math Agent has perfect capability match",
    confidence: 0.98,
    factors: ["Capability Match", "Protocol Support"]
  },
  {
    description: "Final Selection",
    details: "Selected based on highest overall score",
    confidence: 0.95,
    factors: ["Combined Score", "Availability"]
  }
])

<RoutingReasoning
  agentInfo={agentInfo}
  reasoning={structuredReasoning}
  processingTime={1250}
  showByDefault={true} // Show expanded for demo
/>
```

## 🎯 **Key Production Patterns**

1. **Progressive Disclosure**: Show summary first, details on demand
2. **Visual Hierarchy**: Use size, color, and spacing to guide attention  
3. **Semantic Colors**: Confidence levels have consistent color meanings
4. **Smooth Animations**: All state changes are animated for polish
5. **Accessibility**: Proper ARIA labels, keyboard navigation, color contrast
6. **Performance**: `useMemo` and `useCallback` prevent unnecessary re-renders
7. **Graceful Fallbacks**: Handle missing or malformed data elegantly

## 🧪 **Testing Patterns**

```typescript
// Test confidence color logic
describe('RoutingReasoning', () => {
  it('shows green for high confidence', () => {
    render(<RoutingReasoning agentInfo={{ confidence: 0.9 }} />)
    expect(screen.getByText('90%')).toHaveClass('text-green-600')
  })
  
  it('expands on header click', () => {
    render(<RoutingReasoning reasoning="Test reasoning" />)
    fireEvent.click(screen.getByText('AI Routing Decision'))
    expect(screen.getByText('AI Reasoning Steps')).toBeVisible()
  })
  
  it('parses structured reasoning correctly', () => {
    const reasoning = JSON.stringify([{ description: 'Test step' }])
    render(<RoutingReasoning reasoning={reasoning} />)
    // Test parsing logic
  })
})
```

This component demonstrates **production-grade React patterns** for building complex, interactive UI components with smooth animations and excellent UX.

---

**Next**: [04-hooks-implementation-guide.md](./04-hooks-implementation-guide.md) - Custom Hook Deep-Dives  
**Previous**: [02-message-component-analysis.md](./02-message-component-analysis.md)