import React, { useState } from 'react';
import { Zap, Sparkles } from 'lucide-react';

export type QueryMode = 'template' | 'agent';

interface QueryInputProps {
  onSearch: (query: string, mode: QueryMode) => void;
  loading: boolean;
  activeMode: QueryMode;
  onModeChange: (mode: QueryMode) => void;
}

const TEMPLATE_PROMPTS = [
  "How many pending complaints in Road department?",
  "Show open complaints breakdown by workflow status.",
  "Which top 5 departments have the most pending complaints?",
  "How many complaints have breached SLA citywide?",
  "How many pending complaints in Kothrud ward?"
];

const AGENT_PROMPTS = [
  "performance report for SUSHIL CHANDRAKANT MOHITE",
  "how many complaints are pending for the Dept Drainage officer?",
  "how many complaints has been registered in the last month for Baner?",
  "Which ward has the most SLA breaches in last 30 days?"
];

export const QueryInput: React.FC<QueryInputProps> = ({
  onSearch,
  loading,
  activeMode,
  onModeChange
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSearch(text.trim(), activeMode);
    }
  };

  const handlePillClick = (prompt: string) => {
    setText(prompt);
    onSearch(prompt, activeMode);
  };

  const prompts = activeMode === 'template' ? TEMPLATE_PROMPTS : AGENT_PROMPTS;

  return (
    <div className="glass-panel">
      {/* Mode Switcher Toggle Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        background: 'rgba(15, 23, 42, 0.6)',
        padding: '6px',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div style={{ display: 'flex', gap: '6px', width: '100%' }}>
          <button
            type="button"
            onClick={() => onModeChange('template')}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 16px',
              borderRadius: '8px',
              border: activeMode === 'template' ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
              background: activeMode === 'template' ? 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)' : 'transparent',
              color: activeMode === 'template' ? '#38bdf8' : '#94a3b8',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <Zap size={16} />
            <span>⚡ Structural Template Mode</span>
          </button>

          <button
            type="button"
            onClick={() => onModeChange('agent')}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 16px',
              borderRadius: '8px',
              border: activeMode === 'agent' ? '1px solid rgba(192, 132, 252, 0.4)' : '1px solid transparent',
              background: activeMode === 'agent' ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)' : 'transparent',
              color: activeMode === 'agent' ? '#c084fc' : '#94a3b8',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <Sparkles size={16} />
            <span>🧠 Gemini AI Agent Mode ("Anything & Everything")</span>
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="search-box">
        <input
          type="text"
          className="search-input"
          placeholder={
            activeMode === 'template'
              ? "Ask a canonical question (e.g. 'How many pending complaints in Road department?')..."
              : "Ask ANYTHING (e.g. 'performance report for SUSHIL CHANDRAKANT MOHITE' or 'complaints registered last month in Baner')..."
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
          style={
            activeMode === 'agent'
              ? { background: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)' }
              : {}
          }
        >
          {loading ? (activeMode === 'agent' ? 'Gemini Thinking...' : 'Searching...') : (activeMode === 'agent' ? 'Ask Gemini AI' : 'Find Template')}
        </button>
      </form>

      <div className="prompt-pills">
        {prompts.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            className="prompt-pill"
            onClick={() => handlePillClick(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
};

