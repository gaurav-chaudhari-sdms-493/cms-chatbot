import React from 'react';
import { Bot } from 'lucide-react';

export const AnimatedProgress: React.FC = () => {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '20px',
      padding: '8px 14px',
      margin: '8px 0',
      boxShadow: '0 4px 14px rgba(0, 0, 0, 0.06)'
    }}>
      {/* Animated Robot Avatar Icon */}
      <div style={{
        width: '28px',
        height: '28px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#ffffff',
        boxShadow: '0 0 12px rgba(139, 92, 246, 0.4)',
        animation: 'botPulse 1.5s ease-in-out infinite alternate'
      }}>
        <Bot size={16} />
      </div>

      {/* Bouncing Thinking Dots Only (No Text) */}
      <div style={{ display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
        <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent-purple)', animation: 'dotBlink 1.4s infinite 0s' }} />
        <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent-purple)', animation: 'dotBlink 1.4s infinite 0.2s' }} />
        <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent-purple)', animation: 'dotBlink 1.4s infinite 0.4s' }} />
      </div>

      <style>{`
        @keyframes botPulse {
          0% { transform: scale(1); boxShadow: 0 0 6px rgba(139, 92, 246, 0.3); }
          100% { transform: scale(1.1); boxShadow: 0 0 16px rgba(59, 130, 246, 0.6); }
        }
        @keyframes dotBlink {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1.4); }
        }
      `}</style>
    </div>
  );
};
