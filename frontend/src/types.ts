export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: Source[];
  created_at: string;
}

export interface Source {
  id: string;
  source: string;
  title: string;
  similarity: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  model_used: string;
  session_id: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
}