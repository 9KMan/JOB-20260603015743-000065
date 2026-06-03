import React, { useState, useRef, useEffect } from 'react';
import { useAuth, useChat } from './hooks/useChat';
import { Message } from './types';

function App() {
  const { user, loading, error: authError, login, register, logout } = useAuth();
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, loading: chatLoading, sendMessage } = useChat(sessionId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setChatError(null);
    try {
      if (isRegister) {
        await register(email, username, password);
      } else {
        await login(email, password);
      }
    } catch {}
  };

  const handleSendMessage = async (query: string) => {
    if (!query.trim()) return;
    await sendMessage(query);
  };

  if (loading) {
    return (
      <div className="app-container">
        <div className="welcome-message">
          <div className="welcome-icon">🤖</div>
          <div className="welcome-title">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <span className="header-title">Support AI Bot</span>
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span className="header-badge">{user.username}</span>
            <button
              onClick={logout}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                padding: '0.25rem 0.75rem',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
            >
              Logout
            </button>
          </div>
        ) : (
          <span className="header-badge">Anonymous</span>
        )}
      </header>

      {/* Auth Section */}
      {!user && (
        <div className="auth-section">
          <div className="auth-tabs">
            <button
              className={`auth-tab ${!isRegister ? 'active' : ''}`}
              onClick={() => setIsRegister(false)}
            >
              Login
            </button>
            <button
              className={`auth-tab ${isRegister ? 'active' : ''}`}
              onClick={() => setIsRegister(true)}
            >
              Register
            </button>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isRegister && (
              <input
                type="text"
                placeholder="Username"
                className="auth-input"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            )}
            <input
              type="email"
              placeholder="Email"
              className="auth-input"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Password"
              className="auth-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
            <button type="submit" className="auth-btn" disabled={chatLoading}>
              {isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {authError && (
            <div className="error-banner">{authError}</div>
          )}
        </div>
      )}

      {/* Chat Section */}
      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">💬</div>
              <div className="welcome-title">Welcome to Support AI Bot</div>
              <p className="welcome-subtitle">
                Ask me anything about your knowledge base and support tickets.
                I&apos;ll find the most relevant information to help you.
              </p>
            </div>
          ) : (
            <>
              {messages.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {chatLoading && <TypingIndicator />}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {chatError && <div className="error-banner">{chatError}</div>}

        <div className="input-area">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask a question..."
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const target = e.target as HTMLInputElement;
                if (target.value.trim()) {
                  handleSendMessage(target.value);
                  target.value = '';
                }
              }
            }}
            disabled={chatLoading || !user}
          />
          <button
            className="send-btn"
            onClick={() => {
              const input = document.querySelector('.chat-input') as HTMLInputElement;
              if (input?.value.trim()) {
                handleSendMessage(input.value);
                input.value = '';
              }
            }}
            disabled={chatLoading || !user}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        {message.content}
        {message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <div className="sources-title">Sources:</div>
            {message.sources.map((source, idx) => (
              <div key={idx} className="source-item">
                <span className="source-badge">{source.source}</span>
                <span>{source.title}</span>
                <span style={{ color: 'var(--text-secondary)', marginLeft: '0.25rem' }}>
                  ({Math.round(source.similarity * 100)}%)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="typing-indicator">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </div>
  );
}

export default App;