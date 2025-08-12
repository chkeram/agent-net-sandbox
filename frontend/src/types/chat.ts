export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agentId?: string;
  agentName?: string;
  protocol?: string;
  confidence?: number;
  reasoning?: string;
  isStreaming?: boolean;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  error: string | null;
}