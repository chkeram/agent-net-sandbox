import React, { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Send, StopCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  onStopGeneration?: () => void;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  onStopGeneration,
  placeholder = "Type your message..."
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className={clsx(
              "flex-1 resize-none rounded-lg border bg-white dark:bg-gray-900",
              "px-4 py-2 text-sm focus:outline-none focus:ring-2",
              "dark:border-gray-700 dark:text-white",
              isLoading ? "opacity-50 cursor-not-allowed" : "focus:ring-blue-500"
            )}
            style={{ maxHeight: '200px' }}
          />
          
          {isLoading && onStopGeneration ? (
            <button
              onClick={onStopGeneration}
              className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
              aria-label="Stop generation"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={clsx(
                "p-2 rounded-lg transition-colors",
                input.trim() && !isLoading
                  ? "bg-blue-500 text-white hover:bg-blue-600"
                  : "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
              )}
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
        
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};