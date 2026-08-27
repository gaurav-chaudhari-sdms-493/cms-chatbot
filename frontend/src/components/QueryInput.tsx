import React, { useState } from 'react';
import { Send, Sparkles, Loader2 } from 'lucide-react';


export type QueryMode = 'template' | 'agent';

interface QueryInputProps {
  onSearch: (query: string, mode: QueryMode) => void;
  loading: boolean;
  activeMode: QueryMode;
  onModeChange?: (mode: QueryMode) => void;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSearch,
  loading,
  activeMode
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !loading) {
      onSearch(text.trim(), activeMode);
      setText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div style={{
      position: 'sticky',
      bottom: '16px',
      zIndex: 40,
      width: '100%',
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 16px'
    }}>
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '24px',
          padding: '8px 12px 8px 20px',
          boxShadow: '0 12px 32px -8px rgba(0, 0, 0, 0.15)',
          backdropFilter: 'blur(16px)',
          transition: 'all 0.2s ease'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', color: 'var(--accent-purple)' }}>
          <Sparkles size={20} />
        </div>

        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Stark AI anything about PMC officer performance, complaints, or departments..."
          disabled={loading}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: '15px',
            color: 'var(--text-primary)',
            fontFamily: 'inherit'
          }}
        />

        <button
          type="submit"
          disabled={!text.trim() || loading}
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            border: 'none',
            background: text.trim() && !loading
              ? 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)'
              : 'var(--bg-card-hover)',
            color: text.trim() && !loading ? '#ffffff' : 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: text.trim() && !loading ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            boxShadow: text.trim() && !loading ? '0 4px 12px rgba(139, 92, 246, 0.35)' : 'none'
          }}
        >
          {loading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}

        </button>
      </form>
    </div>
  );
};


