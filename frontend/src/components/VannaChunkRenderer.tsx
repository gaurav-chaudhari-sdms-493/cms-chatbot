import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Database, Terminal, Table, BarChart2, CheckCircle2, Loader2, Copy, Check, Search, Download } from 'lucide-react';
import { VannaRichChunk } from '../types';

interface Props {
  chunk: VannaRichChunk;
}

export const VannaChunkRenderer: React.FC<Props> = ({ chunk }) => {
  const { type, data } = chunk;

  switch (type) {
    case 'status_card':
      return <VannaStatusCard data={data} />;
    case 'dataframe':
      return <VannaDataframe data={data} />;
    case 'chart':
      return <VannaChart data={data} />;
    case 'text':
      return <VannaText data={data} />;
    case 'status_bar_update':
    case 'task_tracker_update':
      return <VannaTaskTracker data={data} />;
    default:
      return null;
  }
};

// 1. Status Card Component (SQL Executions / Tool Status)
const VannaStatusCard: React.FC<{ data: any }> = ({ data }) => {
  const [copied, setCopied] = useState(false);
  if (!data) return null;

  const { title, status, description, icon, metadata } = data;
  const sql = metadata?.sql;

  const isSuccess = status === 'success';
  const isRunning = status === 'running';

  const copySql = () => {
    if (sql) {
      navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '12px',
      padding: '14px 16px',
      margin: '12px 0',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: sql ? '10px' : '0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '18px' }}>{icon || '⚙️'}</span>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {title}
            </div>
            {description && (
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {description}
              </div>
            )}
          </div>
        </div>

        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          borderRadius: '20px',
          fontSize: '11px',
          fontWeight: 700,
          background: isSuccess ? 'rgba(16, 185, 129, 0.15)' : (isRunning ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-card-hover)'),
          color: isSuccess ? '#10b981' : (isRunning ? '#3b82f6' : 'var(--text-muted)'),
          border: `1px solid ${isSuccess ? 'rgba(16, 185, 129, 0.3)' : (isRunning ? 'rgba(59, 130, 246, 0.3)' : 'var(--border-color)')}`
        }}>
          {isRunning && <Loader2 size={12} className="animate-spin" />}
          {isSuccess && <CheckCircle2 size={12} />}
          {status ? status.toUpperCase() : 'PENDING'}
        </span>
      </div>

      {sql && (
        <div style={{ marginTop: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Database size={13} /> EXECUTED SQL
            </span>
            <button
              onClick={copySql}
              style={{
                background: 'transparent',
                border: 'none',
                color: copied ? '#10b981' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '11px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre style={{
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '10px 12px',
            fontSize: '12px',
            color: '#38bdf8',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
            margin: 0
          }}>
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
};

// 2. Dataframe Component (Interactive Searchable Data Table)
const VannaDataframe: React.FC<{ data: any }> = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('');
  if (!data) return null;

  const columns: string[] = data.columns || [];
  const rows: Record<string, any>[] = data.data || [];
  const title: string = data.title || 'Query Results';

  const filteredRows = rows.filter(row => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return columns.some(col => String(row[col] ?? '').toLowerCase().includes(term));
  });

  const exportCSV = () => {
    if (!columns.length || !rows.length) return;
    const header = columns.join(',');
    const body = rows.map(r => columns.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([`${header}\n${body}`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '_')}.csv`;
    a.click();
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '14px',
      margin: '16px 0',
      overflow: 'hidden',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.05)'
    }}>
      {/* Header Bar */}
      <div style={{
        padding: '12px 16px',
        background: 'var(--bg-card-hover)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Table size={18} color="var(--accent-blue)" />
          <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
            {title} ({rows.length} rows)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px' }} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search results..."
              style={{
                padding: '6px 12px 6px 30px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--input-bg)',
                color: 'var(--text-primary)',
                fontSize: '12px',
                outline: 'none'
              }}
            />
          </div>

          <button
            onClick={exportCSV}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div style={{ overflowX: 'auto', maxHeight: '350px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--bg-card-hover)', borderBottom: '2px solid var(--border-color)' }}>
              {columns.map(col => (
                <th key={col} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)' }}>
                {columns.map(col => (
                  <td key={col} style={{ padding: '10px 14px', color: 'var(--text-primary)' }}>
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// 3. Chart Component (Plotly Interactive Chart Renderer)
const VannaChart: React.FC<{ data: any }> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data) return;

    const Plotly = (window as any).Plotly;
    if (Plotly && data.data) {
      const chartData = data.data;
      const layout = {
        ...(data.layout || {}),
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: 'var(--text-primary)', family: 'Inter, sans-serif' },
        margin: { t: 40, r: 20, l: 50, b: 50 },
        autosize: true
      };
      Plotly.newPlot(containerRef.current, chartData, layout, { responsive: true, displayModeBar: false });
    }
  }, [data]);

  if (!data) return null;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '14px',
      padding: '16px',
      margin: '16px 0',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.05)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <BarChart2 size={18} color="var(--accent-purple)" />
        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
          {data.title || 'Data Visualization'}
        </span>
      </div>
      <div ref={containerRef} style={{ width: '100%', minHeight: '320px' }} />
    </div>
  );
};

// 4. Text Component (Markdown Text Renderer)
const VannaText: React.FC<{ data: any }> = ({ data }) => {
  if (!data || !data.content) return null;

  return (
    <div style={{
      color: 'var(--text-primary)',
      lineHeight: 1.7,
      fontSize: '15px',
      margin: '12px 0'
    }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {data.content}
      </ReactMarkdown>
    </div>
  );
};

// 5. Task Tracker Component (Progress Status)
const VannaTaskTracker: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return null;

  const message = data.message || data.detail || (data.task ? data.task.title : null);
  if (!message) return null;

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      padding: '6px 12px',
      borderRadius: '20px',
      background: 'var(--bg-card-hover)',
      border: '1px solid var(--border-color)',
      fontSize: '12px',
      color: 'var(--text-secondary)',
      margin: '4px 0'
    }}>
      <Loader2 size={13} className="animate-spin" color="var(--accent-blue)" />
      <span>{message}</span>
    </div>
  );
};
