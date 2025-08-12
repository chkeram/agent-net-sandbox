# Advanced Features 3: AI Routing Transparency - Showing Intelligent Decision Making

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build transparent AI routing displays that show how agents are selected
- Implement expandable reasoning sections with confidence scores
- Create visual decision trees for agent selection process
- Handle complex routing metadata and capability matching
- Build interactive routing insights that help users understand AI decisions

## 🧠 **The AI Routing Transparency Challenge**

Modern agent orchestrators use sophisticated AI to route requests:
- **Capability Analysis**: Matching user queries to agent capabilities
- **Confidence Scoring**: How certain is the AI about the routing decision?
- **Multi-step Reasoning**: Complex decision trees with multiple factors
- **Alternative Agents**: What other options were considered?
- **Performance History**: How past interactions influence routing

**Our goal**: Make **AI routing decisions transparent and educational** for users.

## 🔍 **AI Routing Architecture**

### **Step 1: Routing Decision Types**

```typescript
// src/types/aiRouting.ts
export interface RoutingDecision {
  requestId: string
  query: string
  timestamp: Date
  
  // Primary routing choice
  selectedAgent: {
    id: string
    name: string
    protocol: string
    confidence: number
    reasoningSteps: ReasoningStep[]
  }
  
  // Alternative agents considered
  alternativeAgents: Array<{
    id: string
    name: string
    protocol: string
    confidence: number
    rejectionReason: string
  }>
  
  // Decision factors
  decisionFactors: {
    queryAnalysis: QueryAnalysis
    capabilityMatching: CapabilityMatch[]
    performanceHistory: PerformanceMetric[]
    loadBalancing: LoadBalancingFactor
    contextualFactors: ContextualFactor[]
  }
  
  // Execution metadata
  processingTime: number
  routingStrategy: 'capability_match' | 'performance_based' | 'load_balanced' | 'context_aware'
  llmModel?: string
  temperature?: number
}

export interface ReasoningStep {
  step: number
  type: 'analysis' | 'matching' | 'evaluation' | 'selection' | 'validation'
  description: string
  details: string
  confidence: number
  factors: string[]
  result?: any
}

export interface QueryAnalysis {
  intent: string
  domain: string
  complexity: 'low' | 'medium' | 'high'
  requiredCapabilities: string[]
  keyTerms: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  language: string
  expectedResponseType: 'text' | 'code' | 'calculation' | 'reasoning'
}

export interface CapabilityMatch {
  agentId: string
  agentName: string
  capabilities: Array<{
    name: string
    match: 'perfect' | 'good' | 'partial' | 'none'
    confidence: number
    reasoning: string
  }>
  overallScore: number
  gaps: string[]
}

export interface PerformanceMetric {
  agentId: string
  avgResponseTime: number
  successRate: number
  userSatisfactionScore: number
  recentPerformance: 'excellent' | 'good' | 'fair' | 'poor'
  trendsDescription: string
}

export interface LoadBalancingFactor {
  currentLoad: Record<string, number>
  recommendations: Array<{
    agentId: string
    loadScore: number
    reasoning: string
  }>
  strategy: 'round_robin' | 'least_loaded' | 'performance_weighted'
}

export interface ContextualFactor {
  type: 'user_history' | 'conversation_context' | 'time_of_day' | 'system_state'
  influence: 'high' | 'medium' | 'low'
  description: string
  impact: string
}
```

### **Step 2: Routing Decision Parser**

```typescript
// src/services/routingDecisionParser.ts
export class RoutingDecisionParser {
  /**
   * Parse orchestrator response for routing information
   */
  static parseRoutingDecision(orchestratorResponse: any): RoutingDecision | null {
    try {
      // Check if response contains routing metadata
      const metadata = orchestratorResponse.routing_metadata || 
                      orchestratorResponse.metadata?.routing ||
                      orchestratorResponse._routing

      if (!metadata) {
        return this.createBasicRoutingDecision(orchestratorResponse)
      }

      return {
        requestId: orchestratorResponse.request_id || 'unknown',
        query: metadata.original_query || '',
        timestamp: new Date(orchestratorResponse.timestamp || Date.now()),
        
        selectedAgent: this.parseSelectedAgent(orchestratorResponse, metadata),
        alternativeAgents: this.parseAlternativeAgents(metadata),
        decisionFactors: this.parseDecisionFactors(metadata),
        
        processingTime: metadata.processing_time_ms || 0,
        routingStrategy: metadata.strategy || 'capability_match',
        llmModel: metadata.llm_model,
        temperature: metadata.temperature,
      }
    } catch (error) {
      console.warn('Failed to parse routing decision:', error)
      return this.createBasicRoutingDecision(orchestratorResponse)
    }
  }

  private static parseSelectedAgent(response: any, metadata: any) {
    return {
      id: response.agent_id || 'unknown',
      name: response.agent_name || 'Unknown Agent',
      protocol: response.protocol || 'unknown',
      confidence: metadata.confidence || response.confidence || 0.8,
      reasoningSteps: this.parseReasoningSteps(metadata.reasoning_steps || [])
    }
  }

  private static parseReasoningSteps(steps: any[]): ReasoningStep[] {
    return steps.map((step, index) => ({
      step: index + 1,
      type: step.type || 'analysis',
      description: step.description || 'Processing step',
      details: step.details || '',
      confidence: step.confidence || 0.8,
      factors: step.factors || [],
      result: step.result,
    }))
  }

  private static parseAlternativeAgents(metadata: any) {
    const alternatives = metadata.alternatives || metadata.rejected_agents || []
    
    return alternatives.map((alt: any) => ({
      id: alt.agent_id || alt.id,
      name: alt.agent_name || alt.name || 'Unknown Agent',
      protocol: alt.protocol || 'unknown',
      confidence: alt.confidence || 0.5,
      rejectionReason: alt.rejection_reason || 'Lower confidence score'
    }))
  }

  private static parseDecisionFactors(metadata: any) {
    return {
      queryAnalysis: this.parseQueryAnalysis(metadata.query_analysis || {}),
      capabilityMatching: this.parseCapabilityMatching(metadata.capability_matching || []),
      performanceHistory: this.parsePerformanceHistory(metadata.performance_history || []),
      loadBalancing: this.parseLoadBalancing(metadata.load_balancing || {}),
      contextualFactors: this.parseContextualFactors(metadata.contextual_factors || []),
    }
  }

  private static parseQueryAnalysis(analysis: any): QueryAnalysis {
    return {
      intent: analysis.intent || 'unknown',
      domain: analysis.domain || 'general',
      complexity: analysis.complexity || 'medium',
      requiredCapabilities: analysis.required_capabilities || [],
      keyTerms: analysis.key_terms || [],
      sentiment: analysis.sentiment || 'neutral',
      language: analysis.language || 'en',
      expectedResponseType: analysis.expected_response_type || 'text',
    }
  }

  private static parseCapabilityMatching(matches: any[]): CapabilityMatch[] {
    return matches.map(match => ({
      agentId: match.agent_id,
      agentName: match.agent_name || 'Unknown Agent',
      capabilities: match.capabilities || [],
      overallScore: match.overall_score || 0.5,
      gaps: match.gaps || [],
    }))
  }

  private static parsePerformanceHistory(history: any[]): PerformanceMetric[] {
    return history.map(perf => ({
      agentId: perf.agent_id,
      avgResponseTime: perf.avg_response_time || 1000,
      successRate: perf.success_rate || 0.9,
      userSatisfactionScore: perf.user_satisfaction || 0.8,
      recentPerformance: perf.recent_performance || 'good',
      trendsDescription: perf.trends_description || 'Stable performance',
    }))
  }

  private static parseLoadBalancing(balancing: any): LoadBalancingFactor {
    return {
      currentLoad: balancing.current_load || {},
      recommendations: balancing.recommendations || [],
      strategy: balancing.strategy || 'performance_weighted',
    }
  }

  private static parseContextualFactors(factors: any[]): ContextualFactor[] {
    return factors.map(factor => ({
      type: factor.type || 'system_state',
      influence: factor.influence || 'medium',
      description: factor.description || 'Contextual factor',
      impact: factor.impact || 'Moderate influence on routing',
    }))
  }

  private static createBasicRoutingDecision(response: any): RoutingDecision {
    // Create minimal routing decision from basic response
    return {
      requestId: response.request_id || 'unknown',
      query: 'Unknown query',
      timestamp: new Date(),
      selectedAgent: {
        id: response.agent_id || 'unknown',
        name: response.agent_name || 'Selected Agent',
        protocol: response.protocol || 'unknown',
        confidence: response.confidence || 0.8,
        reasoningSteps: [{
          step: 1,
          type: 'selection',
          description: 'Agent was selected by the orchestrator',
          details: 'No detailed routing information available',
          confidence: response.confidence || 0.8,
          factors: [],
        }]
      },
      alternativeAgents: [],
      decisionFactors: {
        queryAnalysis: {
          intent: 'unknown',
          domain: 'general',
          complexity: 'medium',
          requiredCapabilities: [],
          keyTerms: [],
          sentiment: 'neutral',
          language: 'en',
          expectedResponseType: 'text',
        },
        capabilityMatching: [],
        performanceHistory: [],
        loadBalancing: {
          currentLoad: {},
          recommendations: [],
          strategy: 'capability_match',
        },
        contextualFactors: [],
      },
      processingTime: response.duration_ms || 0,
      routingStrategy: 'capability_match',
    }
  }
}
```

### **Step 3: AI Routing Display Component**

```typescript
// src/components/AIRoutingTransparency.tsx
import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Brain, Target, Clock, Users, Zap, Info } from 'lucide-react'
import { RoutingDecision, ReasoningStep } from '../types/aiRouting'

interface AIRoutingTransparencyProps {
  decision: RoutingDecision
  showByDefault?: boolean
  className?: string
}

export const AIRoutingTransparency: React.FC<AIRoutingTransparencyProps> = ({
  decision,
  showByDefault = false,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(showByDefault)
  const [activeTab, setActiveTab] = useState<'reasoning' | 'alternatives' | 'factors'>('reasoning')

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getConfidenceBadge = (confidence: number) => (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(confidence)}`}>
      {Math.round(confidence * 100)}% confident
    </span>
  )

  return (
    <div className={`ai-routing-transparency bg-blue-50 border border-blue-200 rounded-lg ${className}`}>
      {/* Header - Always visible */}
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-blue-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-blue-600" />
          <div>
            <div className="font-semibold text-blue-800">
              AI Routing Decision
            </div>
            <div className="text-sm text-blue-600">
              Selected <span className="font-medium">{decision.selectedAgent.name}</span> via {decision.routingStrategy.replace('_', ' ')}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {getConfidenceBadge(decision.selectedAgent.confidence)}
          {isExpanded ? <ChevronDown className="w-4 h-4 text-blue-600" /> : <ChevronRight className="w-4 h-4 text-blue-600" />}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-blue-200">
          {/* Tab Navigation */}
          <div className="flex border-b border-blue-200 bg-blue-25">
            {[
              { key: 'reasoning', label: 'AI Reasoning', icon: Brain },
              { key: 'alternatives', label: 'Other Options', icon: Users },
              { key: 'factors', label: 'Decision Factors', icon: Target },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as any)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === key
                    ? 'text-blue-800 bg-white border-b-2 border-blue-600'
                    : 'text-blue-600 hover:text-blue-800 hover:bg-blue-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-4 bg-white">
            {activeTab === 'reasoning' && (
              <ReasoningStepsDisplay steps={decision.selectedAgent.reasoningSteps} />
            )}
            
            {activeTab === 'alternatives' && (
              <AlternativeAgentsDisplay alternatives={decision.alternativeAgents} />
            )}
            
            {activeTab === 'factors' && (
              <DecisionFactorsDisplay factors={decision.decisionFactors} />
            )}
          </div>

          {/* Footer - Processing Info */}
          <div className="px-4 py-2 bg-blue-25 border-t border-blue-200 flex items-center justify-between text-xs text-blue-600">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {decision.processingTime}ms
              </span>
              {decision.llmModel && (
                <span>Model: {decision.llmModel}</span>
              )}
              <span>Strategy: {decision.routingStrategy.replace('_', ' ')}</span>
            </div>
            <span>Request ID: {decision.requestId.slice(-8)}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Reasoning Steps Display
const ReasoningStepsDisplay: React.FC<{ steps: ReasoningStep[] }> = ({ steps }) => (
  <div className="space-y-3">
    <h4 className="font-semibold text-gray-800 mb-3">AI Reasoning Process</h4>
    {steps.map((step, index) => (
      <div key={index} className="relative pl-8">
        {/* Step indicator */}
        <div className="absolute left-0 top-1 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-bold">
          {step.step}
        </div>
        
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-800 capitalize">
              {step.type.replace('_', ' ')}
            </span>
            <span className="text-xs text-gray-500">
              {Math.round(step.confidence * 100)}% confidence
            </span>
          </div>
          
          <p className="text-sm text-gray-700 mb-2">{step.description}</p>
          
          {step.details && (
            <p className="text-xs text-gray-600 mb-2">{step.details}</p>
          )}
          
          {step.factors.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {step.factors.map((factor, i) => (
                <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                  {factor}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {/* Connection line */}
        {index < steps.length - 1 && (
          <div className="absolute left-3 top-8 w-0.5 h-4 bg-blue-200" />
        )}
      </div>
    ))}
  </div>
)

// Alternative Agents Display
const AlternativeAgentsDisplay: React.FC<{ alternatives: any[] }> = ({ alternatives }) => {
  if (alternatives.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>No alternative agents were considered</p>
        <p className="text-sm">The selected agent was the clear best choice</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h4 className="font-semibold text-gray-800 mb-3">Other Agents Considered</h4>
      {alternatives.map((agent, index) => (
        <div key={index} className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="font-medium text-gray-800">{agent.name}</span>
              <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                {agent.protocol.toUpperCase()}
              </span>
            </div>
            <span className={`px-2 py-1 rounded text-xs ${
              agent.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
            }`}>
              {Math.round(agent.confidence * 100)}%
            </span>
          </div>
          <p className="text-sm text-gray-600">{agent.rejectionReason}</p>
        </div>
      ))}
    </div>
  )
}

// Decision Factors Display
const DecisionFactorsDisplay: React.FC<{ factors: any }> = ({ factors }) => (
  <div className="space-y-4">
    <h4 className="font-semibold text-gray-800 mb-3">Decision Analysis</h4>
    
    {/* Query Analysis */}
    <div className="border rounded-lg p-3">
      <h5 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
        <Target className="w-4 h-4" />
        Query Analysis
      </h5>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-600">Intent:</span>
          <span className="ml-2 font-medium">{factors.queryAnalysis.intent}</span>
        </div>
        <div>
          <span className="text-gray-600">Domain:</span>
          <span className="ml-2 font-medium">{factors.queryAnalysis.domain}</span>
        </div>
        <div>
          <span className="text-gray-600">Complexity:</span>
          <span className={`ml-2 px-2 py-1 rounded text-xs ${
            factors.queryAnalysis.complexity === 'high' ? 'bg-red-100 text-red-800' :
            factors.queryAnalysis.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            {factors.queryAnalysis.complexity}
          </span>
        </div>
        <div>
          <span className="text-gray-600">Response Type:</span>
          <span className="ml-2 font-medium">{factors.queryAnalysis.expectedResponseType}</span>
        </div>
      </div>
      
      {factors.queryAnalysis.requiredCapabilities.length > 0 && (
        <div className="mt-3">
          <span className="text-gray-600 text-sm">Required Capabilities:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {factors.queryAnalysis.requiredCapabilities.map((cap: string, i: number) => (
              <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                {cap}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>

    {/* Capability Matching */}
    {factors.capabilityMatching.length > 0 && (
      <div className="border rounded-lg p-3">
        <h5 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Capability Matching
        </h5>
        <div className="space-y-2">
          {factors.capabilityMatching.map((match: any, index: number) => (
            <div key={index} className="bg-gray-50 rounded p-2">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-sm">{match.agentName}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  match.overallScore >= 0.8 ? 'bg-green-100 text-green-800' :
                  match.overallScore >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {Math.round(match.overallScore * 100)}% match
                </span>
              </div>
              {match.gaps.length > 0 && (
                <div className="text-xs text-gray-600">
                  Gaps: {match.gaps.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Contextual Factors */}
    {factors.contextualFactors.length > 0 && (
      <div className="border rounded-lg p-3">
        <h5 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
          <Info className="w-4 h-4" />
          Contextual Factors
        </h5>
        <div className="space-y-2">
          {factors.contextualFactors.map((factor: any, index: number) => (
            <div key={index} className="flex items-start gap-3">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                factor.influence === 'high' ? 'bg-red-100 text-red-800' :
                factor.influence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {factor.influence}
              </span>
              <div className="flex-1">
                <div className="font-medium text-sm">{factor.description}</div>
                <div className="text-xs text-gray-600">{factor.impact}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
)
```

### **Step 4: Integration with Chat Interface**

```typescript
// src/components/EnhancedMessage.tsx - With AI routing transparency
import React from 'react'
import { AIRoutingTransparency } from './AIRoutingTransparency'
import { RoutingDecisionParser } from '../services/routingDecisionParser'

interface EnhancedMessageProps {
  message: {
    id: string
    content: string
    agentName: string
    timestamp: Date
    orchestratorResponse?: any
  }
  showRoutingByDefault?: boolean
}

export const EnhancedMessage: React.FC<EnhancedMessageProps> = ({
  message,
  showRoutingByDefault = false,
}) => {
  // Parse routing decision from orchestrator response
  const routingDecision = message.orchestratorResponse 
    ? RoutingDecisionParser.parseRoutingDecision(message.orchestratorResponse)
    : null

  return (
    <div className="enhanced-message space-y-3">
      {/* AI Routing Transparency */}
      {routingDecision && (
        <AIRoutingTransparency 
          decision={routingDecision}
          showByDefault={showRoutingByDefault}
        />
      )}

      {/* Message Content */}
      <div className="message-content bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="font-semibold">{message.agentName}</span>
          <span className="text-xs text-gray-500">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
        
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap">{message.content}</pre>
        </div>
      </div>
    </div>
  )
}
```

### **Step 5: Routing Analytics Dashboard**

```typescript
// src/components/RoutingAnalyticsDashboard.tsx
import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Brain, TrendingUp, Users, Clock } from 'lucide-react'

interface RoutingAnalyticsProps {
  decisions: RoutingDecision[]
  className?: string
}

export const RoutingAnalyticsDashboard: React.FC<RoutingAnalyticsProps> = ({
  decisions,
  className = '',
}) => {
  const [analytics, setAnalytics] = useState<any>({})

  useEffect(() => {
    const computed = computeAnalytics(decisions)
    setAnalytics(computed)
  }, [decisions])

  if (decisions.length === 0) {
    return (
      <div className={`routing-analytics-dashboard text-center py-8 text-gray-500 ${className}`}>
        <Brain className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>No routing decisions to analyze</p>
      </div>
    )
  }

  return (
    <div className={`routing-analytics-dashboard bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
        <Brain className="w-5 h-5 text-blue-600" />
        AI Routing Analytics
      </h3>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Avg Confidence</span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {Math.round(analytics.avgConfidence * 100)}%
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Agents Used</span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            {analytics.uniqueAgents || 0}
          </div>
        </div>

        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">Avg Time</span>
          </div>
          <div className="text-2xl font-bold text-yellow-900">
            {Math.round(analytics.avgProcessingTime)}ms
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-800">Total Decisions</span>
          </div>
          <div className="text-2xl font-bold text-purple-900">
            {decisions.length}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Usage Chart */}
        <div>
          <h4 className="font-medium mb-3">Agent Selection Frequency</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={analytics.agentUsage || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Routing Strategy Distribution */}
        <div>
          <h4 className="font-medium mb-3">Routing Strategies</h4>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={analytics.strategyDistribution || []}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
                label
              >
                {(analytics.strategyDistribution || []).map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={`hsl(${index * 60}, 70%, 60%)`} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Confidence Distribution */}
      <div className="mt-6">
        <h4 className="font-medium mb-3">Confidence Score Distribution</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={analytics.confidenceDistribution || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="range" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#10B981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function computeAnalytics(decisions: RoutingDecision[]) {
  if (decisions.length === 0) return {}

  // Basic metrics
  const avgConfidence = decisions.reduce((sum, d) => sum + d.selectedAgent.confidence, 0) / decisions.length
  const avgProcessingTime = decisions.reduce((sum, d) => sum + d.processingTime, 0) / decisions.length
  const uniqueAgents = new Set(decisions.map(d => d.selectedAgent.id)).size

  // Agent usage frequency
  const agentCounts: Record<string, number> = {}
  decisions.forEach(d => {
    const name = d.selectedAgent.name
    agentCounts[name] = (agentCounts[name] || 0) + 1
  })
  const agentUsage = Object.entries(agentCounts).map(([name, count]) => ({ name, count }))

  // Strategy distribution
  const strategyCounts: Record<string, number> = {}
  decisions.forEach(d => {
    const strategy = d.routingStrategy.replace('_', ' ')
    strategyCounts[strategy] = (strategyCounts[strategy] || 0) + 1
  })
  const strategyDistribution = Object.entries(strategyCounts).map(([name, count]) => ({ name, count }))

  // Confidence distribution
  const confidenceRanges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
  const confidenceCounts = [0, 0, 0, 0, 0]
  decisions.forEach(d => {
    const conf = d.selectedAgent.confidence * 100
    if (conf <= 20) confidenceCounts[0]++
    else if (conf <= 40) confidenceCounts[1]++
    else if (conf <= 60) confidenceCounts[2]++
    else if (conf <= 80) confidenceCounts[3]++
    else confidenceCounts[4]++
  })
  const confidenceDistribution = confidenceRanges.map((range, i) => ({
    range,
    count: confidenceCounts[i]
  }))

  return {
    avgConfidence,
    avgProcessingTime,
    uniqueAgents,
    agentUsage,
    strategyDistribution,
    confidenceDistribution,
  }
}
```

## 🎯 **Usage Examples**

### **Basic Integration**
```typescript
// In your chat container
const [messages, setMessages] = useState<MessageWithRouting[]>([])

const handleStreamComplete = (response: any) => {
  const newMessage = {
    id: Date.now().toString(),
    content: response.content,
    agentName: response.agent_name,
    timestamp: new Date(),
    orchestratorResponse: response, // Include full response for routing analysis
  }
  
  setMessages(prev => [...prev, newMessage])
}

return (
  <div className="chat-container">
    {messages.map(message => (
      <EnhancedMessage
        key={message.id}
        message={message}
        showRoutingByDefault={false} // Let users expand to see details
      />
    ))}
  </div>
)
```

### **Analytics Integration**
```typescript
// Routing analytics page
const RoutingInsightsPage: React.FC = () => {
  const [routingHistory, setRoutingHistory] = useState<RoutingDecision[]>([])

  useEffect(() => {
    // Load routing decisions from storage/API
    loadRoutingHistory().then(setRoutingHistory)
  }, [])

  return (
    <div className="routing-insights-page">
      <h1 className="text-2xl font-bold mb-6">AI Routing Insights</h1>
      <RoutingAnalyticsDashboard decisions={routingHistory} />
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Transparency builds trust** - Users appreciate understanding AI decisions
2. **Progressive disclosure works** - Start collapsed, allow expansion for details
3. **Visual reasoning helps** - Step-by-step decision trees are intuitive
4. **Context matters** - Show why alternatives were rejected
5. **Analytics provide insights** - Track routing patterns over time
6. **Performance impact is minimal** - Routing data is small and cacheable
7. **Educational value is high** - Users learn about AI capabilities

---

**Next**: [04-message-persistence-system.md](./04-message-persistence-system.md) - Advanced State Management

**Previous**: [02-message-actions-system.md](./02-message-actions-system.md)