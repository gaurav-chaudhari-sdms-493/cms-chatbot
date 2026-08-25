import React, { useRef, useEffect } from 'react';
import { User, Sparkles, Loader2 } from 'lucide-react';
import { ChatMessageResponse, AgentQueryResponse } from '../types';
import { MarkdownReport } from './MarkdownReport';

interface Props {
  messages: ChatMessageResponse[];
  loading: boolean;
  questionText: string;
}

export const ChatStream: React.FC<Props> = ({ messages, loading, questionText }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return null;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', margin: '20px 0' }}>
      {messages.map((msg) => {
        if (msg.sender === 'user') {
          return (
            <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%)',
                border: '1px solid rgba(168, 85, 247, 0.4)',
                borderRadius: '16px 16px 4px 16px',
                padding: '14px 20px',
                maxWidth: '75%',
                color: '#f8fafc',
                fontSize: '15px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
              }}>
                {msg.content}
              </div>
              <div style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <User size={18} color="#ffffff" />
              </div>
            </div>
          );
        } else {
          // Agent message
          const agentResponse: AgentQueryResponse = {
            question: questionText || 'Query Result',
            markdown_report: msg.content,
            sql_used: msg.sql_used || '',
            execution_time_ms: msg.execution_time_ms || 0,
            retry_count: 0,
            status: 'SUCCESS'
          };
          return (
            <div key={msg.id} style={{ width: '100%' }}>
              <MarkdownReport data={agentResponse} />
            </div>
          );
        }
      })}

      {/* Loading Indicator */}
      {loading && (
        <div style={{
          background: 'rgba(30, 41, 59, 0.7)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#c084fc'
        }}>
          <Loader2 size={24} className="animate-spin" style={{ animation: 'spin 1.5s linear infinite' }} />
          <div>
            <div style={{ fontWeight: 600, fontSize: '15px', color: '#f8fafc' }}>
              Gemini 3.6 Flash Analyzing & Verification Loop Active...
            </div>
            <div style={{ fontSize: '13px', color: '#94a3b8' }}>
              Generating SQL, executing against PMC PostgreSQL DB, and self-correcting if needed...
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
