export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  imageUrl?: string;
  reference_links?: string[];
  relevant_docs?: any[];
}

export interface Conversation {
  id: number;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}
