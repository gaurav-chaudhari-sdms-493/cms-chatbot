import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Info, X, Database, Cpu, Clock, Copy, Check, Sparkles, Layers, CheckCircle2 } from 'lucide-react';
import { AgentQueryResponse } from '../types';

interface Props {
  data: AgentQueryResponse;
}

export const MarkdownReport: React.FC<Props> = ({ data }) => {
  const [showTemplateInfo, setShowTemplateInfo] = useState(false);
  const [copiedSql, setCopiedSql] = useState(false);

  const handleCopySql = () => {
    if (data.sql_used) {
      navigator.clipboard.writeText(data.sql_used);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '16px',
      padding: '20px 24px',
      boxShadow: '0 8px 24px -6px rgba(0, 0, 0, 0.08)',
      marginBottom: '16px',
      position: 'relative'
    }}>
      {/* Header Bar with Agent Badge and Template Info (i) Button */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: '14px',
        marginBottom: '14px',
        borderBottom: '1px solid var(--border-color)',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        {/* Agent Identity Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
            borderRadius: '8px',
            padding: '5px 7px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={14} color="#ffffff" />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            PMC Analytics AI Assistant
          </span>
        </div>

        {/* Action Controls & Info (i) Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {data.execution_time_ms > 0 && (
            <span style={{
              fontSize: '11px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'var(--bg-card-hover)',
              padding: '3px 8px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)'
            }}>
              <Clock size={12} color="var(--text-secondary)" />
              {data.execution_time_ms} ms
            </span>
          )}

          {/* Info (i) Button */}
          <button
            onClick={() => setShowTemplateInfo(!showTemplateInfo)}
            style={{
              background: showTemplateInfo
                ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)'
                : 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.35)',
              borderRadius: '8px',
              padding: '4px 10px',
              color: 'var(--accent-purple)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 600,
              transition: 'all 0.2s ease',
              boxShadow: showTemplateInfo ? '0 2px 8px rgba(139, 92, 246, 0.25)' : 'none'
            }}
            title="View LLM Candidate Templates & SQL Query Details"
          >
            {showTemplateInfo ? (
              <X size={14} color="var(--accent-purple)" />
            ) : (
              <Info size={14} color="var(--accent-purple)" />
            )}
            <span>{showTemplateInfo ? 'Close Info' : 'Info (i)'}</span>
          </button>
        </div>
      </div>

      {/* Collapsible Info (i) Template Details Card */}
      {showTemplateInfo && (
        <div style={{
          background: 'var(--bg-card-hover)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '12px',
          padding: '16px 18px',
          marginBottom: '18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          animation: 'fadeIn 0.2s ease-in-out'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={16} color="var(--accent-purple)" />
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                LLM Query Template Selection & Candidate Info
              </span>
            </div>
            <span style={{
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              color: '#ffffff',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 700,
              letterSpacing: '0.04em'
            }}>
              {data.template_id || 'OPENROUTER_DYNAMIC'}
            </span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            fontSize: '12px',
            color: 'var(--text-secondary)'
          }}>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>Selected Template:</strong>{' '}
              <code>{data.template_id || 'Canonical Dynamic Match'}</code>
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>Retrieval Model:</strong>{' '}
              E5 Multilingual Dense + BM25 RRF
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>LLM Engine:</strong>{' '}
              OpenRouter Pipeline
            </div>
          </div>

          {/* Top Candidate Templates Provided to OpenRouter LLM */}
          {data.candidate_templates && data.candidate_templates.length > 0 && (
            <div style={{ marginTop: '6px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                <Layers size={14} color="var(--accent-purple)" />
                TOP CANDIDATE TEMPLATES PROVIDED TO LLM ({data.candidate_templates.length}):
              </span>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {data.candidate_templates.map((cand, idx) => {
                  const isSelected = cand.template_id === data.template_id;
                  return (
                    <div
                      key={idx}
                      style={{
                        background: isSelected ? 'rgba(139, 92, 246, 0.12)' : 'var(--bg-card)',
                        border: isSelected ? '1px solid rgba(139, 92, 246, 0.4)' : '1px solid var(--border-color)',
                        borderRadius: '8px',
                        padding: '10px 14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px'
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <span style={{
                            fontWeight: 700,
                            fontSize: '12px',
                            color: isSelected ? 'var(--accent-purple)' : 'var(--text-primary)'
                          }}>
                            #{idx + 1} {cand.template_id}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                            ({cand.intent})
                          </span>
                          {isSelected && (
                            <span style={{
                              background: '#10b981',
                              color: '#ffffff',
                              fontSize: '10px',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '6px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <CheckCircle2 size={10} /> SELECTED BY LLM
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          "{cand.question_template}"
                        </div>
                      </div>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        RRF Score: {cand.score}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Executed SQL query preview if present */}
          {data.sql_used && (
            <div style={{ marginTop: '6px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '6px'
              }}>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Database size={12} color="var(--accent-blue)" />
                  EXECUTED PARAMETERIZED SQL
                </span>
                <button
                  onClick={handleCopySql}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: copiedSql ? '#10b981' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '11px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {copiedSql ? <Check size={12} /> : <Copy size={12} />}
                  {copiedSql ? 'Copied' : 'Copy SQL'}
                </button>
              </div>
              <pre style={{
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '10px 12px',
                margin: 0,
                fontSize: '11px',
                color: '#38bdf8',
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                overflowX: 'auto',
                maxHeight: '160px'
              }}>
                {data.sql_used}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Main Markdown Content Body */}
      <div className="agent-markdown-body" style={{ color: 'var(--text-primary)', lineHeight: 1.7, fontSize: '15px' }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {data.markdown_report}
        </ReactMarkdown>
      </div>
    </div>
  );
};
