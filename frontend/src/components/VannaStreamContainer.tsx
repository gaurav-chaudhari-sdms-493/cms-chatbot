import React, { useState, useEffect, useRef } from 'react';
import { VannaRichChunk } from '../types';
import { VannaChunkRenderer } from './VannaChunkRenderer';
import { User, Sparkles, Send, Loader2 } from 'lucide-react';

interface StreamMessage {
  id: string;
  sender: 'user' | 'vanna';
  text?: string;
  chunks?: VannaRichChunk[];
  timestamp: Date;
}

interface Props {
  conversationId?: string;
  initialQuestion?: string;
}

export const VannaStreamContainer: React.FC<Props> = ({
  conversationId = 'session-ui-vanna',
  initialQuestion
}) => {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuestion) {
      handleSend(initialQuestion);
    }
  }, [initialQuestion]);

  const handleSend = async (questionText: string) => {
    if (!questionText.trim() || loading) return;

    const userMsg: StreamMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: questionText,
      timestamp: new Date()
    };

    const vannaMsgId = `vanna-${Date.now()}`;
    const vannaMsg: StreamMessage = {
      id: vannaMsgId,
      sender: 'vanna',
      chunks: [],
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg, vannaMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/vanna/v2/chat_sse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cookie': 'vanna_email=admin@example.com'
        },
        body: JSON.stringify({
          message: questionText,
          conversation_id: conversationId
        })
      });

      if (!response.body) {
        throw new Error('No response body stream');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;

          const dataStr = trimmed.slice(6).trim();
          if (dataStr === '[DONE]') break;

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.rich) {
              const richChunk: VannaRichChunk = parsed.rich;

              setMessages(prev => prev.map(m => {
                if (m.id === vannaMsgId) {
                  // Prevent duplicate chunks by ID or update existing chunk
                  const existingIdx = (m.chunks || []).findIndex(c => c.id === richChunk.id);
                  let updatedChunks = [...(m.chunks || [])];
                  if (existingIdx >= 0) {
                    updatedChunks[existingIdx] = richChunk;
                  } else {
                    updatedChunks.push(richChunk);
                  }
                  return { ...m, chunks: updatedChunks };
                }
                return m;
              }));
            }
          } catch (err) {
            // Ignore parse errors for partial chunks
          }
        }
      }
    } catch (err) {
      console.error('SSE Stream error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '900px', margin: '0 auto', padding: '16px' }}>
      
      {/* Stream Messages List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
            <Sparkles size={40} color="var(--accent-purple)" style={{ marginBottom: '12px' }} />
            <h2 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Vanna AI Live Streaming Direct Engine
            </h2>
            <p style={{ fontSize: '14px', maxWidth: '500px', margin: '8px auto 0' }}>
              Submits requests to <code>/api/vanna/v2/chat_sse</code> and directly renders Vanna SSE status cards, interactive dataframes, Plotly charts & text blocks.
            </p>
          </div>
        )}

        {messages.map(msg => {
          if (msg.sender === 'user') {
            return (
              <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <div style={{
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%)',
                  border: '1px solid rgba(168, 85, 247, 0.4)',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '14px 20px',
                  maxWidth: '75%',
                  color: 'var(--text-primary)',
                  fontSize: '15px'
                }}>
                  {msg.text}
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
            return (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
                {msg.chunks && msg.chunks.map(chunk => (
                  <VannaChunkRenderer key={chunk.id || Math.random().toString()} chunk={chunk} />
                ))}
              </div>
            );
          }
        })}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
            <Loader2 size={16} className="animate-spin" color="var(--accent-purple)" />
            <span>Streaming response chunks from Vanna AI...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(input); }} style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Vanna AI anything..."
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '14px',
            outline: 'none'
          }}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            padding: '14px 24px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-indigo))',
            border: 'none',
            color: '#ffffff',
            fontWeight: 600,
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !input.trim() ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Send size={16} /> Send
        </button>
      </form>
    </div>
  );
};
