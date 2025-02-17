// types.ts
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'error';
  feedback?: 'good' | 'bad' | null;
  sources?: Source[];
}

export interface Source {
  text: string;
  url: string;
}

export interface ChatState {
  messages: Message[];
  sources: Source[];
  isTyping: boolean;
  error: string | null;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setTyping: (typing: boolean) => void;
  setFeedback: (messageId: string, feedback: 'good' | 'bad' | null) => Promise<void>;
}