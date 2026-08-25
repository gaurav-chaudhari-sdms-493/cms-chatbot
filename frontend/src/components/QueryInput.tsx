import React, { useState } from 'react';

interface QueryInputProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

const SAMPLE_PROMPTS = [
  "How many pending complaints in Road department?",
  "Show open complaints breakdown by workflow status.",
  "Which top 5 departments have the most pending complaints?",
  "How many complaints have breached SLA citywide?",
  "How many pending complaints in Kothrud ward?"
];

export const QueryInput: React.FC<QueryInputProps> = ({ onSearch, loading }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSearch(text.trim());
    }
  };

  const handlePillClick = (prompt: string) => {
    setText(prompt);
    onSearch(prompt);
  };

  return (
    <div className="glass-panel">
      <form onSubmit={handleSubmit} className="search-box">
        <input
          type="text"
          className="search-input"
          placeholder="Ask a question in natural language (e.g. 'How many pending complaints in Road department?')..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Searching...' : 'Find Template'}
        </button>
      </form>

      <div className="prompt-pills">
        {SAMPLE_PROMPTS.map((prompt, idx) => (
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
