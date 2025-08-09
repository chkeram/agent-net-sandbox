import React, { useState, useCallback, useEffect } from 'react';
import { MessageList } from './MessageList.tsx';
import { ChatInput } from './ChatInput.tsx';
import type { Message } from '../../types/chat.ts';
import { useOrchestrator } from '../../hooks/useOrchestrator.ts';
import { v4 as uuidv4 } from 'uuid';
import { AlertCircle, WifiOff, RefreshCw } from 'lucide-react';

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const { 
    isHealthy, 
    isLoading, 
    error, 
    agents,
    processMessage, 
    checkHealth,
    refreshAgents,
    clearError 
  } = useOrchestrator();

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
      } catch (error) {
        console.error('Failed to load messages from localStorage:', error);
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]);

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

    // Process through orchestrator
    const response = await processMessage(content);

    if (response) {
      // Success - add assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.content || 'No response received',
        timestamp: new Date(),
        agentId: response.agent_id,
        agentName: response.agent_name,
        protocol: response.protocol,
        confidence: response.confidence,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } else {
      // Error - add error message
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        error: error || 'Failed to process message. Please try again.',
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  }, [processMessage, error, clearError]);

  const handleStopGeneration = useCallback(() => {
    // TODO: Implement abort controller for streaming
    console.log('Stop generation requested');
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    localStorage.removeItem('chat-messages');
  }, []);

  const handleRetry = useCallback(async () => {
    await checkHealth();
    await refreshAgents();
  }, [checkHealth, refreshAgents]);

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
          
          {/* Connection error banner */}
          {!isHealthy && (
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
      <MessageList messages={messages} isLoading={isLoading} />
      
      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onStopGeneration={handleStopGeneration}
        placeholder={isHealthy ? "Type your message..." : "Waiting for connection..."}
      />
    </div>
  );
};