import React, { useState, useCallback, useEffect } from 'react';
import { MessageList } from './MessageList.tsx';
import { ChatInput } from './ChatInput.tsx';
import type { Message } from '../../types/chat.ts';
import { useStreamingOrchestrator } from '../../hooks/useStreamingOrchestrator.ts';
import { OrchestratorAPI, type ProcessResponse } from '../../services/orchestratorApi.ts';
import { v4 as uuidv4 } from 'uuid';
import { AlertCircle, WifiOff, RefreshCw, Bot, Zap, Brain } from 'lucide-react';

export const StreamingChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [regularApi] = useState(() => new OrchestratorAPI());
  const { 
    isHealthy, 
    isLoading, 
    error, 
    agents,
    streamingState,
    processMessageStream,
    checkHealth,
    refreshAgents,
    clearError,
    abortStream
  } = useStreamingOrchestrator();

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat-messages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })));
      } catch (e) {
        console.error('Failed to parse saved messages:', e);
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]);

  // Update streaming message as chunks arrive
  useEffect(() => {
    if (streamingState.accumulatedResponse) {
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
          // Update the streaming message
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: streamingState.accumulatedResponse,
            }
          ];
        }
        return prev;
      });
    }
  }, [streamingState.accumulatedResponse]);

  // Complete the streaming message
  useEffect(() => {
    if (streamingState.streamPhase === 'completed') {
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
          // Mark as completed
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              isStreaming: false,
              agentId: streamingState.routingInfo?.agentId,
              agentName: streamingState.routingInfo?.agentName,
              protocol: streamingState.routingInfo?.protocol,
              confidence: streamingState.routingInfo?.confidence,
              reasoning: streamingState.routingInfo?.reasoning,
            }
          ];
        }
        return prev;
      });
    }
  }, [streamingState.streamPhase]);

  const handleSendMessage = useCallback(async (content: string) => {
    // Clear any previous errors
    clearError();

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    // Add placeholder assistant message for streaming
    const assistantMessage: Message = {
      id: uuidv4(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, assistantMessage]);

    // Process through streaming orchestrator, fallback to regular API if streaming fails
    let response: ProcessResponse | undefined;
    try {
      await processMessageStream(content);
      return; // Streaming handled the response
    } catch (streamError) {
      console.warn('Streaming failed, falling back to regular API:', streamError);
      
      // Update the assistant message to show fallback
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: '⚠️ Streaming unavailable, using standard mode...',
            }
          ];
        }
        return prev;
      });

      // Use regular API as fallback
      response = await regularApi.processMessage(content);
      
      if (response) {
        // Update with actual response
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            const updatedMessage = {
              ...lastMessage,
              content: response?.content || 'No response received',
              agentId: response?.agent_id,
              agentName: response?.agent_name,
              protocol: response?.protocol,
              confidence: response?.confidence,
              reasoning: response?.reasoning,
              isStreaming: false,
            };
            return [
              ...prev.slice(0, -1),
              updatedMessage
            ];
          }
          return prev;
        });
      }
    }

    if (!response && error) {
      // Update the assistant message with error
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: '',
              error: error || 'Failed to process message. Please try again.',
              isStreaming: false,
            }
          ];
        }
        return prev;
      });
    }
  }, [processMessageStream, regularApi, error, clearError]);

  const handleStopGeneration = useCallback(() => {
    abortStream();
  }, [abortStream]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    localStorage.removeItem('chat-messages');
  }, []);

  const handleRetryMessage = useCallback(async (messageId: string) => {
    // Find the failed message and the user message that preceded it
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) return;

    const failedMessage = messages[messageIndex];
    if (failedMessage.role !== 'assistant') return;

    // Find the user message that this was a response to
    let userMessage: Message | null = null;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMessage = messages[i];
        break;
      }
    }

    if (!userMessage) return;

    // Remove all messages from the failed message onward
    setMessages(prev => prev.slice(0, messageIndex));

    // Retry the user's message
    await handleSendMessage(userMessage.content);
  }, [messages, handleSendMessage]);

  const handleCopyMessage = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // You could show a toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  }, []);

  const handleRetry = useCallback(async () => {
    await checkHealth();
    await refreshAgents();
  }, [checkHealth, refreshAgents]);

  const getStreamingIndicator = () => {
    if (!streamingState.isStreaming) return null;

    switch (streamingState.streamPhase) {
      case 'routing':
        return (
          <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <Brain className="w-4 h-4 animate-pulse" />
            <span>Analyzing your request...</span>
          </div>
        );
      case 'executing':
        return (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <Zap className="w-4 h-4 animate-pulse" />
            <span>Connecting to {streamingState.routingInfo?.agentName || 'agent'}...</span>
          </div>
        );
      case 'streaming':
        return (
          <div className="flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400">
            <Bot className="w-4 h-4 animate-pulse" />
            <span>{streamingState.routingInfo?.agentName || 'Agent'} is responding...</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="border-b dark:border-gray-700 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold dark:text-white">
                Agent Network Sandbox
              </h1>
              {/* Health indicator */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  isHealthy ? 'bg-green-500' : 'bg-red-500'
                } animate-pulse`} />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {isHealthy ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Agent count */}
              {agents.length > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {agents.length} agent{agents.length !== 1 ? 's' : ''} available
                </span>
              )}
              
              {/* Refresh button */}
              <button
                onClick={handleRetry}
                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                title="Refresh connection"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              
              {/* Clear button */}
              <button
                onClick={clearMessages}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                Clear chat
              </button>
            </div>
          </div>
          
          {/* Streaming indicator */}
          {streamingState.isStreaming && (
            <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              {getStreamingIndicator()}
              {streamingState.routingInfo?.confidence && (
                <div className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                  Confidence: {Math.round(streamingState.routingInfo.confidence * 100)}%
                </div>
              )}
            </div>
          )}
          
          {/* Connection error banner */}
          {!isHealthy && !streamingState.isStreaming && (
            <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
              <WifiOff className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-sm text-red-700 dark:text-red-300">
                Orchestrator is not connected. Please ensure Docker services are running.
              </span>
              <button
                onClick={handleRetry}
                className="ml-auto text-sm text-red-600 dark:text-red-400 hover:underline"
              >
                Retry
              </button>
            </div>
          )}
          
          {/* API error banner */}
          {error && !isHealthy && (
            <div className="mt-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                {error}
              </span>
            </div>
          )}
        </div>
      </div>
      
      {/* Messages */}
      <MessageList 
        messages={messages} 
        isLoading={isLoading || streamingState.isStreaming} 
        isStreaming={streamingState.isStreaming}
        onRetryMessage={handleRetryMessage}
        onCopyMessage={handleCopyMessage}
      />
      
      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading || streamingState.isStreaming}
        onStopGeneration={handleStopGeneration}
        placeholder={isHealthy ? "Type your message..." : "Waiting for connection..."}
      />
    </div>
  );
};