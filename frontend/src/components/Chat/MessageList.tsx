import React, { useEffect, useRef } from 'react';
import { Message } from './Message.tsx';
import type { Message as MessageType } from '../../types/chat.ts';

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
  isStreaming?: boolean; // Global streaming state to hide individual typing indicators
  onRetryMessage?: (messageId: string) => void;
  onCopyMessage?: (content: string) => void;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, isStreaming = false, onRetryMessage, onCopyMessage }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <p className="text-lg mb-2">Welcome to Agent Network Sandbox</p>
            <p className="text-sm">Start a conversation with the multi-protocol orchestrator</p>
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <Message 
              key={message.id} 
              message={message} 
              hideTypingIndicator={isStreaming}
              onRetry={onRetryMessage}
              onCopy={onCopyMessage}
            />
          ))}
          {isLoading && (
            <div className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-900">
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <div className="animate-pulse w-5 h-5 bg-white rounded-full" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
};