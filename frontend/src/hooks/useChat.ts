import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Message, User } from '../types';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = apiService.getToken();
    if (token) {
      apiService.getMe()
        .then((userData: unknown) => setUser(userData as User))
        .catch(() => {
          apiService.setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      await apiService.login(email, password);
      const userData = await apiService.getMe();
      setUser(userData as User);
    } catch (err) {
      setError((err as Error).message);
      throw err;
    }
  };

  const register = async (email: string, username: string, password: string, fullName?: string) => {
    setError(null);
    try {
      await apiService.register(email, username, password, fullName);
      await login(email, password);
    } catch (err) {
      setError((err as Error).message);
      throw err;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
  };

  return { user, loading, error, login, register, logout };
}

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, [sessionId]);

  const loadHistory = async () => {
    try {
      const history = await apiService.getHistory(sessionId) as Message[];
      setMessages(history);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const sendMessage = async (query: string) => {
    setLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await apiService.sendMessage(query, sessionId) as {
        answer: string;
        sources: Message['sources'];
        model_used: string;
        session_id: string;
      };

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError((err as Error).message);
      // Remove the optimistically added user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    try {
      await apiService.clearHistory(sessionId);
      setMessages([]);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  return { messages, loading, error, sendMessage, clearHistory };
}