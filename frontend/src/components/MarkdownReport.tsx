import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AgentQueryResponse } from '../types';
import { Sparkles, Code2, Clock, RefreshCw, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  data: AgentQueryResponse;
}

export const MarkdownReport: React.FC<Props> = ({ data }) => {
  const [showSql, setShowSql] = useState(false);

  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      padding: '28px',
      marginTop: '24px',
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)'
    }}>
      {/* Top Status & Metadata Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '16px',
        marginBottom: '24px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={18} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#c084fc', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Gemini 3.6 Flash Autonomous AI Report
            </div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
              {data.question}
            </div>
          </div>
        </div>

        {/* Stats Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#94a3b8'
          }}>
            <Clock size={14} color="#38bdf8" />
            <span>{(data.execution_time_ms / 1000).toFixed(2)}s</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '13px',
            color: data.retry_count > 0 ? '#f59e0b' : '#34d399'
          }}>
            <RefreshCw size={14} />
            <span>{data.retry_count === 0 ? 'Verified 1st Attempt' : `${data.retry_count} Self-Correction Retries`}</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: data.status === 'SUCCESS' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(248, 113, 113, 0.15)',
            border: `1px solid ${data.status === 'SUCCESS' ? 'rgba(52, 211, 153, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            color: data.status === 'SUCCESS' ? '#34d399' : '#f87171'
          }}>
            {data.status === 'SUCCESS' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
            <span>{data.status === 'SUCCESS' ? 'Verified Answer' : 'Resolution Notice'}</span>
          </div>
        </div>
      </div>

      {/* Main Markdown Body */}
      <div className="agent-markdown-body" style={{ color: '#e2e8f0', lineHeight: 1.7, fontSize: '15px' }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {data.markdown_report}
        </ReactMarkdown>
      </div>

      {/* SQL Transparency Audit Drawer */}
      {data.sql_used && (
        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <button
            onClick={() => setShowSql(!showSql)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '8px 14px',
              color: '#94a3b8',
              fontSize: '13px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <Code2 size={15} color="#c084fc" />
            <span>{showSql ? 'Hide Audit SQL Query' : 'View Verified SQL Query Executed'}</span>
            {showSql ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {showSql && (
            <div style={{
              marginTop: '12px',
              background: '#0f172a',
              borderRadius: '8px',
              padding: '16px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase' }}>
                PostgreSQL Execution Query (Read-Only)
              </div>
              <pre style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
                color: '#38bdf8',
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {data.sql_used}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
