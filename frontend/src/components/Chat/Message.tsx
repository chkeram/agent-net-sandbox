import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, AlertCircle } from 'lucide-react';
import type { Message as MessageType } from '../../types/chat.ts';
import { clsx } from 'clsx';

interface MessageProps {
  message: MessageType;
  hideTypingIndicator?: boolean; // Hide typing dots if global streaming is active
}

export const Message: React.FC<MessageProps> = ({ message, hideTypingIndicator = false }) => {
  const isUser = message.role === 'user';
  const isError = !!message.error;
  const isStreaming = !!message.isStreaming;

  return (
    <div className={clsx('flex gap-3 p-4', isUser ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900')}>
      <div className="flex-shrink-0">
        <div className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-blue-500' : isError ? 'bg-red-500' : 'bg-green-500'
        )}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : isError ? (
            <AlertCircle className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">
            {isUser ? 'You' : message.agentName || 'Assistant'}
          </span>
          {message.protocol && (
            <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              {message.protocol.toUpperCase()}
            </span>
          )}
          {message.agentId && message.agentId !== message.agentName && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ({message.agentId})
            </span>
          )}
          {message.confidence !== undefined && message.confidence > 0 && (
            <span className="text-xs text-gray-500">
              {Math.round(message.confidence * 100)}% confidence
            </span>
          )}
        </div>
        
        {isError ? (
          <div className="text-red-600 dark:text-red-400">
            {message.error}
          </div>
        ) : isStreaming && !message.content && !hideTypingIndicator ? (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Thinking...</span>
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <div className="relative group">
                      <SyntaxHighlighter
                        style={tomorrow as any}
                        language={match[1]}
                        PreTag="div"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                      <button
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 text-xs bg-gray-700 text-white rounded"
                        onClick={() => navigator.clipboard.writeText(String(children))}
                      >
                        Copy
                      </button>
                    </div>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
          {isStreaming && (
            <span className="flex items-center gap-1 text-blue-500 dark:text-blue-400">
              <span className="animate-pulse">●</span>
              <span>Streaming...</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};