import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Info, X, Database, Cpu, Clock, Copy, Check, Sparkles, Layers, CheckCircle2, Send, Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Loader2 } from 'lucide-react';
import { AgentQueryResponse } from '../types';
import { fetchReferenceOptions, fetchQueryPage } from '../services/api';

interface Props {
  data: AgentQueryResponse;
  onSelectOption?: (optionLabel: string) => void;
}

// SQL Pretty Formatter Helper
const formatSql = (sql: string): string => {
  if (!sql) return '';
  let str = sql.trim();
  if (!str.includes('\n')) {
    str = str.replace(/\s+/g, ' ');
    str = str.replace(/\bSELECT\s+/gi, 'SELECT\n  ');
    str = str.replace(/\bFROM\s+/gi, '\nFROM ');
    str = str.replace(/\b((?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN)\s+/gi, '\n$1 ');
    str = str.replace(/\bON\s+/gi, '\n  ON ');
    str = str.replace(/\bWHERE\s+/gi, '\nWHERE ');
    str = str.replace(/\bAND\s+/gi, '\n  AND ');
    str = str.replace(/\bOR\s+/gi, '\n  OR ');
    str = str.replace(/\bGROUP\s+BY\s+/gi, '\nGROUP BY ');
    str = str.replace(/\bORDER\s+BY\s+/gi, '\nORDER BY ');
    str = str.replace(/\bLIMIT\s+/gi, '\nLIMIT ');
    str = str.replace(/\bHAVING\s+/gi, '\nHAVING ');

    const fromIndex = str.indexOf('\nFROM ');
    if (fromIndex > 0) {
      const selectPart = str.substring(0, fromIndex);
      const restPart = str.substring(fromIndex);
      const formattedSelect = selectPart.replace(/,\s*/g, ',\n  ');
      str = formattedSelect + restPart;
    }
  }
  return str.trim();
};

// Vibrant IDE-Style SQL Syntax Shower Component
const SqlSyntaxHighlighter: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);
  const formattedCode = formatSql(code);

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tokenRegex = /(--[^\n]*|\/\*[\s\S]*?\*\/|'(?:''|[^'])*'|"(?:""|[^"])*"|\b(?:SELECT|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|CROSS|ON|AND|OR|GROUP BY|GROUP|ORDER BY|ORDER|BY|HAVING|LIMIT|OFFSET|AS|IN|IS|NOT|NULL|LIKE|ILIKE|CASE|WHEN|THEN|ELSE|END|UNION|ALL|INSERT|UPDATE|DELETE|INTO|VALUES|SET)\b|\b(?:LOWER|UPPER|COUNT|SUM|AVG|MAX|MIN|COALESCE|DATE_TRUNC|CONCAT|NOW|CAST|SUBSTRING)\b|\b\d+(?:\.\d+)?\b|[a-zA-Z_][a-zA-Z0-9_]*|\s+|[^\s\a-zA-Z0-9_])/gi;

  const keywords = new Set([
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'CROSS',
    'ON', 'AND', 'OR', 'GROUP', 'ORDER', 'BY', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'IN',
    'IS', 'NOT', 'NULL', 'LIKE', 'ILIKE', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'UNION',
    'ALL', 'INSERT', 'UPDATE', 'DELETE', 'INTO', 'VALUES', 'SET'
  ]);

  const functions = new Set([
    'LOWER', 'UPPER', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'COALESCE', 'DATE_TRUNC', 'CONCAT', 'NOW', 'CAST', 'SUBSTRING'
  ]);

  const matches = formattedCode.match(tokenRegex) || [formattedCode];

  const highlightedNodes = matches.map((token, index) => {
    const upper = token.toUpperCase();
    if (token.startsWith('--') || token.startsWith('/*')) {
      return <span key={index} style={{ color: '#64748b', fontStyle: 'italic' }}>{token}</span>;
    }
    if ((token.startsWith("'") && token.endsWith("'")) || (token.startsWith('"') && token.endsWith('"'))) {
      return <span key={index} style={{ color: '#34d399', fontWeight: 600 }}>{token}</span>;
    }
    if (/^\d+(?:\.\d+)?$/.test(token)) {
      return <span key={index} style={{ color: '#f87171', fontWeight: 600 }}>{token}</span>;
    }
    if (keywords.has(upper)) {
      return <span key={index} style={{ color: '#a78bfa', fontWeight: 700 }}>{token}</span>;
    }
    if (functions.has(upper)) {
      return <span key={index} style={{ color: '#fbbf24', fontWeight: 700 }}>{token}</span>;
    }
    if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(token)) {
      return <span key={index} style={{ color: '#38bdf8' }}>{token}</span>;
    }
    return <span key={index} style={{ color: '#94a3b8' }}>{token}</span>;
  });

  return (
    <div style={{
      position: 'relative',
      background: '#0f172a',
      border: '1px solid rgba(255, 255, 255, 0.15)',
      borderRadius: '12px',
      overflow: 'hidden',
      margin: '10px 0',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)'
    }}>
      {/* IDE Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 14px',
        background: 'rgba(255, 255, 255, 0.05)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        fontSize: '11px',
        color: '#94a3b8',
        fontFamily: 'sans-serif'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          <span style={{ fontWeight: 700, marginLeft: '8px', color: '#cbd5e1', letterSpacing: '0.04em', fontSize: '11px' }}>EXECUTED SQL</span>
        </div>
        <button
          onClick={handleCopy}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '6px',
            padding: '3px 8px',
            color: copied ? '#10b981' : '#e2e8f0',
            cursor: 'pointer',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontWeight: 600,
            transition: 'all 0.2s'
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      <pre style={{
        margin: 0,
        padding: '14px 16px',
        fontSize: '13px',
        lineHeight: '1.65',
        fontFamily: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace",
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        overflowX: 'auto',
        color: '#f8fafc',
        maxHeight: '280px'
      }}>
        <code>{highlightedNodes}</code>
      </pre>
    </div>
  );
};

export const MarkdownReport: React.FC<Props> = ({ data, onSelectOption }) => {
  const [showTemplateInfo, setShowTemplateInfo] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const handleCopyReport = () => {
    if (data.markdown_report) {
      navigator.clipboard.writeText(data.markdown_report);
      setCopiedReport(true);
      setTimeout(() => setCopiedReport(false), 2000);
    }
  };

  return (
    <div style={{
      background: 'transparent',
      border: 'none',
      borderRadius: '0px',
      padding: '4px 0 16px 0',
      marginBottom: '20px',
      position: 'relative',
      width: '100%'
    }}>

      {/* Main Markdown Content Body */}
      <div style={{ position: 'relative', margin: '12px 0' }}>
        <div
          className="agent-markdown-body"
          style={{
            color: 'var(--text-primary)',
            lineHeight: 1.7,
            fontSize: '15px',
            position: 'relative'
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ node, ...props }) => (
                <SearchableTable questionText={data.question} reportText={data.markdown_report} sqlUsed={data.sql_used} serverTotal={data.total_records}>{props.children}</SearchableTable>
              ),
              th: ({ node, ...props }) => (
                <th style={{ background: 'var(--bg-card-hover)', padding: '12px 14px', fontWeight: 700, fontSize: '12.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-primary)', borderBottom: '2px solid var(--border-color)', textAlign: 'left', whiteSpace: 'nowrap' }} {...props} />
              ),
              td: ({ node, ...props }) => (
                <SmartTableCell>{props.children}</SmartTableCell>
              ),
              code: ({ node, inline, className, children, ...props }: any) => {
                const codeString = String(children).replace(/\n$/, '');
                if (!inline && (codeString.toLowerCase().includes('select') || codeString.toLowerCase().includes('from') || className?.includes('sql'))) {
                  return <SqlSyntaxHighlighter code={codeString} />;
                }
                return inline ? (
                  <code style={{ background: 'var(--bg-card-hover)', padding: '2px 6px', borderRadius: '4px', fontSize: '13px', color: 'var(--accent-purple)', fontWeight: 600 }} {...props}>{children}</code>
                ) : (
                  <pre style={{ background: '#0f172a', color: '#f8fafc', padding: '12px 14px', borderRadius: '8px', fontSize: '13px', overflowX: 'auto' }}><code>{children}</code></pre>
                );
              }
            }}
          >
            {data.markdown_report}
          </ReactMarkdown>
        </div>
      </div>

      {/* BOTTOM FOOTER METADATA & ACTIONS (ChatGPT Style Bottom Bar) */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '12px',
        paddingTop: '10px',
        borderTop: '1px solid rgba(0, 0, 0, 0.06)',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        {/* Left Action Buttons: Copy Response */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleCopyReport}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '5px 12px',
              color: copiedReport ? '#10b981' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 500,
              transition: 'all 0.2s ease'
            }}
            title="Copy Report Response"
          >
            {copiedReport ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
            <span>{copiedReport ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>

        {/* Right Action Metadata: Execution Speed & Info (i) Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {data.execution_time_ms > 0 && (
            <span style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'var(--bg-card-hover)',
              padding: '3px 8px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)'
            }}>
              <Clock size={12} color="var(--text-muted)" />
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

      {/* Collapsible Info (i) Details Card - Modern SQL Syntax Shower View */}
      {showTemplateInfo && (
        <div style={{
          background: 'var(--bg-card-hover)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '12px',
          padding: '14px 16px',
          marginTop: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          animation: 'fadeIn 0.2s ease-in-out'
        }}>
          {data.sql_used && (
            <SqlSyntaxHighlighter code={data.sql_used} />
          )}
        </div>
      )}

      {/* Render Picklist Component if message is a Follow-Up Question */}
      {data.markdown_report && (data.markdown_report.includes('Follow-Up Question') || data.markdown_report.includes('❓')) && (
        <ChatPicklistFollowup reportText={data.markdown_report} onSelect={onSelectOption} />
      )}
    </div>
  );
};

// Plotly Dynamic Multi-Series Comparison Chart Renderer for Markdown Tables
const TablePlotlyChart: React.FC<{
  labels: string[];
  seriesList: { name: string; values: number[] }[];
  labelName: string;
  chartType: 'bar' | 'pie' | 'line';
}> = ({ labels, seriesList, labelName, chartType }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !seriesList.length) return;
    const Plotly = (window as any).Plotly;

    if (Plotly) {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const fontColor = isDark ? '#e2e8f0' : '#1e293b';

      const palette = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6', '#06b6d4', '#84cc16'];

      let dataTraces: any[] = [];

      if (chartType === 'pie') {
        const primarySeries = seriesList[0];
        dataTraces = [{
          labels: labels,
          values: primarySeries.values,
          type: 'pie',
          name: primarySeries.name.replace(/_/g, ' '),
          textinfo: 'label+percent',
          hoverinfo: 'label+value+percent',
          marker: { colors: palette }
        }];
      } else if (chartType === 'line') {
        dataTraces = seriesList.map((s, idx) => ({
          x: labels,
          y: s.values,
          name: s.name.replace(/_/g, ' '),
          type: 'scatter',
          mode: 'lines+markers',
          marker: { color: palette[idx % palette.length], size: 8 },
          line: { color: palette[idx % palette.length], width: 3 }
        }));
      } else {
        // Grouped Comparison Bar Chart
        dataTraces = seriesList.map((s, idx) => ({
          x: labels,
          y: s.values,
          name: s.name.replace(/_/g, ' '),
          type: 'bar',
          marker: { color: palette[idx % palette.length] },
          hovertemplate: `<b>%{x}</b><br>${s.name.replace(/_/g, ' ')}: %{y:,}<extra></extra>`
        }));
      }

      const chartTitle = seriesList.length > 1
        ? `Comparison (${seriesList.map(s => s.name.replace(/_/g, ' ')).join(' vs ')}) by ${labelName.replace(/_/g, ' ')}`
        : `${seriesList[0].name.replace(/_/g, ' ')} by ${labelName.replace(/_/g, ' ')}`;

      const layout = {
        title: {
          text: chartTitle,
          font: { color: fontColor, size: 15, family: 'Inter, sans-serif' }
        },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: fontColor, family: 'Inter, sans-serif' },
        barmode: 'group',
        legend: { orientation: 'h', y: 1.18, x: 0, font: { color: fontColor } },
        margin: { t: 50, r: 20, l: 60, b: labels.some(l => l.length > 10) ? 90 : 50 },
        xaxis: {
          title: labelName.replace(/_/g, ' '),
          tickangle: labels.some(l => l.length > 10) ? -40 : 0,
          color: fontColor
        },
        yaxis: {
          title: 'Value',
          color: fontColor
        },
        autosize: true
      };

      Plotly.newPlot(containerRef.current, dataTraces, layout, { responsive: true, displayModeBar: false });
    }
  }, [labels, seriesList, labelName, chartType]);

  return (
    <div style={{ width: '100%', minHeight: '380px', padding: '12px', background: 'var(--bg-card)' }}>
      <div ref={containerRef} style={{ width: '100%', minHeight: '360px' }} />
    </div>
  );
};

// Dynamic Real-Time Searchable Table & Auto-Charting Component
const SearchableTable: React.FC<{ children?: React.ReactNode; questionText?: string; reportText?: string; sqlUsed?: string; serverTotal?: number | null }> = ({ children, questionText, reportText, sqlUsed, serverTotal }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const childrenArray = React.Children.toArray(children);
  const thead = childrenArray.find(
    (child: any) => child?.type === 'thead' || child?.props?.mdxType === 'thead'
  );
  const tbody = childrenArray.find(
    (child: any) => child?.type === 'tbody' || child?.props?.mdxType === 'tbody'
  );

  const tbodyChildren = tbody && (tbody as any).props?.children;
  const initialRows = React.Children.toArray(tbodyChildren);

  const getNodeText = (node: React.ReactNode): string => {
    if (!node) return '';
    if (typeof node === 'string' || typeof node === 'number') return String(node);
    if (Array.isArray(node)) return node.map(getNodeText).join(' ');
    if (typeof node === 'object' && node !== null && 'props' in (node as any)) {
      return getNodeText((node as any).props.children);
    }
    return '';
  };

  // Parse Headers & Row Values for Charting
  const trHead = thead && (thead as any).props?.children;
  const thNodes = trHead ? React.Children.toArray((trHead as any).props?.children || trHead) : [];
  const headers = thNodes.map(node => getNodeText(node).trim());

  const initialDataRows: string[][] = initialRows.map(rNode => {
    const tdNodes = React.Children.toArray((rNode as any).props?.children || []);
    return tdNodes.map(td => getNodeText(td).trim());
  });

  // Extract server total records count if present in report text, question text, or serverTotal prop
  const combinedText = (reportText || '') + ' ' + (questionText || '');
  const totalMatch = combinedText.match(/(?:total records|TOTAL_RECORDS:)(?:[^\d]*)([\d,]+)/i);
  const parsedTotalMatch = totalMatch ? parseInt(totalMatch[1].replace(/,/g, ''), 10) : 0;
  const initialTotal = (serverTotal !== undefined && serverTotal !== null && serverTotal > 0)
    ? serverTotal
    : (parsedTotalMatch > 0 ? parsedTotalMatch : initialRows.length);

  const [activeRows, setActiveRows] = useState<React.ReactNode[]>(initialRows);
  const [activeDataRows, setActiveDataRows] = useState<string[][]>(initialDataRows);
  const [serverTotalRecords, setServerTotalRecords] = useState<number>(initialTotal);
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [isPageLoading, setIsPageLoading] = useState(false);

  useEffect(() => {
    setActiveRows(initialRows);
    setActiveDataRows(initialDataRows);
    const pTotal = (serverTotal !== undefined && serverTotal !== null && serverTotal > 0)
      ? serverTotal
      : (parsedTotalMatch > 0 ? parsedTotalMatch : 0);
    if (pTotal > 0) {
      setServerTotalRecords(pTotal);
    } else if (sqlUsed) {
      fetchQueryPage(sqlUsed, 1, 25).then(res => {
        if (res.total_records > 0) setServerTotalRecords(res.total_records);
      }).catch(() => {});
    }
  }, [children, serverTotal, reportText, questionText, sqlUsed]);

  const handlePageChange = async (newPage: number, newPageSize: number = rowsPerPage) => {
    if (!sqlUsed) {
      setCurrentPage(newPage);
      setRowsPerPage(newPageSize);
      return;
    }
    setIsPageLoading(true);
    try {
      const res = await fetchQueryPage(sqlUsed, newPage, newPageSize);
      const newRowElements = res.rows.map((rowArr, rIdx) => (
        <tr key={rIdx}>
          {rowArr.map((val, cIdx) => (
            <SmartTableCell key={cIdx}>{val}</SmartTableCell>
          ))}
        </tr>
      ));
      setActiveRows(newRowElements);
      setActiveDataRows(res.rows);
      setServerTotalRecords(res.total_records);
      setCurrentPage(res.page);
      setRowsPerPage(res.page_size);
    } catch (err) {
      console.error('Server pagination error:', err);
    } finally {
      setIsPageLoading(false);
    }
  };

  // Identify label column & ALL metric numeric columns
  let labelColIdx = -1;
  let numericColIdxs: number[] = [];

  if (headers.length >= 2 && activeDataRows.length > 0) {
    const numCols: number[] = [];
    const strCols: number[] = [];

    headers.forEach((headerName, c) => {
      const isNum = activeDataRows.every(r => r[c] !== undefined && r[c] !== null && r[c] !== '' && !isNaN(Number(r[c].replace(/,/g, '').replace(/%/g, ''))));
      const isIdColumn = /(_id|\bid\b|token_no|complaint_number|pincode|zipcode)/i.test(headerName);
      if (isNum && !isIdColumn) numCols.push(c);
      else strCols.push(c);
    });

    if (strCols.length > 0 && numCols.length > 0) {
      labelColIdx = strCols[0];
      numericColIdxs = numCols;
    } else if (numCols.length >= 2) {
      labelColIdx = numCols[0];
      numericColIdxs = numCols.slice(1);
    } else if (headers.length >= 2) {
      labelColIdx = 0;
      numericColIdxs = [1];
    }
  }

  // Determine initial view mode based on question keywords
  const qLower = (questionText || '').toLowerCase();
  const isChartRequested = qLower.includes('chart') || qLower.includes('graph') || qLower.includes('plot') || qLower.includes('bar') || qLower.includes('pie') || qLower.includes('distribution') || qLower.includes('trend') || qLower.includes('trends') || qLower.includes('comparison') || qLower.includes('compare') || qLower.includes('monthly') || qLower.includes('timeline') || qLower.includes('over time') || numericColIdxs.length > 1;

  let initialMode: 'table' | 'bar' | 'pie' | 'line' = 'table';
  if (isChartRequested && labelColIdx !== -1 && numericColIdxs.length > 0) {
    if (qLower.includes('pie')) initialMode = 'pie';
    else if (qLower.includes('line') || qLower.includes('trend') || qLower.includes('monthly') || qLower.includes('timeline') || qLower.includes('over time') || qLower.includes('comparison') || qLower.includes('compare')) initialMode = 'line';
    else initialMode = 'bar';
  }

  const [viewMode, setViewMode] = useState<'table' | 'bar' | 'pie' | 'line'>(initialMode);

  const filteredRows = activeRows.filter((rowNode) => {
    if (!searchTerm.trim()) return true;
    const rowText = getNodeText(rowNode).toLowerCase();
    return rowText.includes(searchTerm.toLowerCase().trim());
  });

  const effectiveTotal = Math.max(serverTotalRecords, filteredRows.length);
  const totalPages = Math.ceil(effectiveTotal / rowsPerPage) || 1;
  const safeCurrentPage = Math.min(Math.max(currentPage, 1), totalPages);

  const isServerPaginated = Boolean(sqlUsed && serverTotalRecords > activeRows.length);
  const startIndex = (safeCurrentPage - 1) * rowsPerPage;
  const endIndex = Math.min(startIndex + activeRows.length, effectiveTotal);
  const paginatedRows = isServerPaginated ? filteredRows : filteredRows.slice(startIndex, endIndex);

  // Prepare chart series arrays
  const chartLabels = activeDataRows.map(r => r[labelColIdx] || '');
  const seriesList = numericColIdxs.map(cIdx => ({
    name: headers[cIdx] || `Metric ${cIdx}`,
    values: activeDataRows.map(r => Number((r[cIdx] || '0').replace(/,/g, '').replace(/%/g, '')))
  }));
  const canChart = labelColIdx !== -1 && seriesList.length > 0 && chartLabels.length > 0;

  return (
    <div style={{
      margin: '16px 0',
      borderRadius: '12px',
      border: '1px solid var(--border-color)',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
      background: 'var(--bg-card)',
      overflow: 'hidden'
    }}>
      {/* Table & Chart Toolbar Bar */}
      <div style={{
        padding: '10px 14px',
        background: 'var(--bg-card-hover)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        {/* View Mode Switcher Chips */}
        {canChart && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => setViewMode('table')}
              style={{
                background: viewMode === 'table' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                border: viewMode === 'table' ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                color: viewMode === 'table' ? 'var(--accent-blue)' : 'var(--text-secondary)',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              📋 Table View
            </button>
            <button
              onClick={() => setViewMode('bar')}
              style={{
                background: viewMode === 'bar' ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                border: viewMode === 'bar' ? '1px solid var(--accent-purple)' : '1px solid var(--border-color)',
                color: viewMode === 'bar' ? 'var(--accent-purple)' : 'var(--text-secondary)',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              📊 Bar Chart
            </button>
            <button
              onClick={() => setViewMode('line')}
              style={{
                background: viewMode === 'line' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                border: viewMode === 'line' ? '1px solid #6366f1' : '1px solid var(--border-color)',
                color: viewMode === 'line' ? '#6366f1' : 'var(--text-secondary)',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              📈 Line Trend
            </button>
            <button
              onClick={() => setViewMode('pie')}
              style={{
                background: viewMode === 'pie' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                border: viewMode === 'pie' ? '1px solid #10b981' : '1px solid var(--border-color)',
                color: viewMode === 'pie' ? '#10b981' : 'var(--text-secondary)',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              🥧 Pie Chart
            </button>
          </div>
        )}

        {/* Search input (Table View Only) */}
        {viewMode === 'table' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '200px', position: 'relative' }}>
            <Search size={15} color="var(--accent-blue)" style={{ position: 'absolute', left: '10px' }} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search table by any keyword..."
              style={{
                width: '100%',
                padding: '5px 30px 5px 32px',
                borderRadius: '8px',
                background: 'var(--input-bg)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                fontSize: '12px',
                outline: 'none'
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                style={{
                  position: 'absolute',
                  right: '8px',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>
        )}

        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {effectiveTotal.toLocaleString()} records
        </div>
      </div>

      {/* Render Chart or Table */}
      {viewMode !== 'table' && canChart ? (
        <TablePlotlyChart
          labels={chartLabels}
          seriesList={seriesList}
          labelName={headers[labelColIdx] || 'Label'}
          chartType={viewMode}
        />
      ) : (
        <>
          <div style={{
            overflowX: 'auto',
            overflowY: 'auto',
            maxHeight: '440px',
            width: '100%',
            position: 'relative'
          }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, fontSize: '13.5px' }}>
              {thead}
              <tbody>
                {paginatedRows.length > 0 ? (
                  paginatedRows
                ) : (
                  <tr>
                    <td colSpan={100} style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
                      🔍 No table records match "<strong>{searchTerm}</strong>".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* JetBrains DataGrip Floating Bottom Pagination Bar */}
          {effectiveTotal > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 14px',
              background: 'var(--bg-card-hover)',
              borderTop: '1px solid var(--border-color)',
              fontSize: '12px',
              color: 'var(--text-secondary)',
              flexWrap: 'wrap',
              gap: '10px'
            }}>
              {/* Left: Range Info & Per Page Selector */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>
                  Showing <strong>{startIndex + 1} - {endIndex}</strong> of <strong>{effectiveTotal.toLocaleString()}</strong> records
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Per page:</span>
                  <select
                    value={rowsPerPage}
                    onChange={(e) => handlePageChange(1, Number(e.target.value))}
                    style={{
                      background: 'var(--input-bg)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      padding: '2px 6px',
                      fontSize: '11.5px',
                      cursor: 'pointer',
                      outline: 'none'
                    }}
                  >
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={250}>250</option>
                    <option value={500}>500</option>
                  </select>
                </div>
              </div>

              {/* Right: DataGrip Control Capsule */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                background: 'var(--input-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '3px 8px'
              }}>
                {isPageLoading && (
                  <span style={{ fontSize: '11px', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '4px', marginRight: '6px', fontWeight: 600 }}>
                    <Loader2 size={12} className="animate-spin" /> Loading...
                  </span>
                )}

                {/* First Page |< */}
                <button
                  disabled={currentPage <= 1 || isPageLoading}
                  onClick={() => handlePageChange(1)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage <= 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
                    padding: '2px 4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="First Page"
                >
                  <ChevronsLeft size={14} />
                </button>

                {/* Previous Page < */}
                <button
                  disabled={currentPage <= 1 || isPageLoading}
                  onClick={() => handlePageChange(currentPage - 1)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage <= 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
                    padding: '2px 4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="Previous Page"
                >
                  <ChevronLeft size={14} />
                </button>

                <span style={{ fontSize: '11.5px', fontWeight: 600, padding: '0 6px', color: 'var(--accent-blue)' }}>
                  Page {currentPage} of {totalPages.toLocaleString()}
                </span>

                {/* Next Page > */}
                <button
                  disabled={currentPage >= totalPages || isPageLoading}
                  onClick={() => handlePageChange(currentPage + 1)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage >= totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
                    padding: '2px 4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="Next Page"
                >
                  <ChevronRight size={14} />
                </button>

                {/* Last Page >| */}
                <button
                  disabled={currentPage >= totalPages || isPageLoading}
                  onClick={() => handlePageChange(totalPages)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage >= totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
                    padding: '2px 4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="Last Page"
                >
                  <ChevronsRight size={14} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Column-Wise Extender / Minimizer Table Cell Component
const SmartTableCell: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const extractText = (node: React.ReactNode): string => {
    if (!node) return '';
    if (typeof node === 'string' || typeof node === 'number') return String(node);
    if (Array.isArray(node)) return node.map(extractText).join(' ');
    if (typeof node === 'object' && node !== null && 'props' in (node as any) && (node as any).props.children) {
      return extractText((node as any).props.children);
    }
    return '';
  };

  const rawText = extractText(children).trim();
  const cleanSingleLine = rawText.replace(/\s+/g, ' ');
  const isLongText = cleanSingleLine.length > 55;
  const isShortCode = /^(W\d+|CMS\d+|DMS\d+|\d{4}-\d{2}-\d{2}|\d+:\d+:\d+|Resolved|Pending|Closed|Open|\d+)$/i.test(cleanSingleLine);

  return (
    <td
      style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--border-color)',
        color: 'var(--text-primary)',
        verticalAlign: 'top',
        fontSize: '13px',
        lineHeight: 1.5,
        whiteSpace: isShortCode ? 'nowrap' : 'normal',
        wordBreak: isShortCode ? 'normal' : 'break-word',
        minWidth: isShortCode ? 'auto' : (isExpanded ? '280px' : '150px'),
        maxWidth: isExpanded ? '450px' : '220px'
      }}
    >
      {!isLongText ? (
        children
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{
            maxHeight: isExpanded ? '140px' : 'none',
            overflowY: isExpanded ? 'auto' : 'visible',
            fontSize: '12.5px',
            lineHeight: '1.45'
          }}>
            {isExpanded ? rawText : `${cleanSingleLine.slice(0, 52)}...`}
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            style={{
              alignSelf: 'flex-start',
              background: isExpanded ? 'rgba(239, 68, 68, 0.12)' : 'rgba(59, 130, 246, 0.12)',
              color: isExpanded ? '#f87171' : 'var(--accent-blue)',
              border: 'none',
              borderRadius: '4px',
              padding: '2px 7px',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '3px',
              marginTop: '3px'
            }}
            title={isExpanded ? 'Minimise column text' : 'Extend full text'}
          >
            {isExpanded ? '[-] Minimise' : '[+] Extend'}
          </button>
        </div>
      )}
    </td>
  );
};

const ChatPicklistFollowup: React.FC<{
  reportText: string;
  onSelect?: (val: string) => void;
}> = ({ reportText, onSelect }) => {
  const [sourceTable, setSourceTable] = useState<string | null>(null);
  const [options, setOptions] = useState<{ id: any; label: string }[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string>('');
  const [intentAction, setIntentAction] = useState<string>('pending_complaints');
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    const textLower = reportText.toLowerCase();
    let table = null;
    if (textLower.includes('department')) table = 'department_master';
    else if (textLower.includes('ward')) table = 'ward_master';
    else if (textLower.includes('zone')) table = 'zone_master';
    else if (textLower.includes('category')) table = 'category_master';
    else if (textLower.includes('status')) table = 'status_master';

    // Extract single-quoted entity from follow-up text (e.g. 'Hadapsar - Mundhwa')
    const match = reportText.match(/'([^']+)'/);
    let extracted = match && match[1] ? match[1] : '';
    if (extracted) {
      setSelectedEntity(extracted);
    }

    if (table) {
      setSourceTable(table);
      fetchReferenceOptions(table)
        .then((res) => {
          const opts = res.options || [];
          setOptions(opts);
          if (!extracted && opts.length > 0) {
            setSelectedEntity(opts[0].label);
          }
        })
        .catch(console.error);
    }
  }, [reportText]);

  if (!sourceTable && !selectedEntity) return null;

  const typeName = sourceTable ? sourceTable.replace('_master', '').replace('_', ' ') : 'entity';

  const getIntentQuery = (): string => {
    const entity = selectedEntity || 'this area';
    switch (intentAction) {
      case 'pending_complaints':
        return `Show pending complaints for ${entity}`;
      case 'sla_breaches':
        return `Show SLA breached complaints for ${entity}`;
      case 'officer_performance':
        return `Show officer performance and workload for ${entity}`;
      case 'category_breakdown':
        return `Show top complaint categories for ${entity}`;
      default:
        return `Show pending complaints for ${entity}`;
    }
  };

  const handleSubmit = () => {
    if (isSubmitted || !onSelect) return;
    const finalQuery = getIntentQuery();
    setIsSubmitted(true);
    onSelect(finalQuery);
  };

  return (
    <div style={{
      marginTop: '16px',
      padding: '16px 18px',
      borderRadius: '12px',
      background: 'var(--bg-card-hover)',
      border: '1px solid rgba(139, 92, 246, 0.3)',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06)',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={16} color="var(--accent-purple)" />
          Configure & Submit Follow-Up Query:
        </span>
        {sourceTable && (
          <span style={{ fontSize: '11px', background: 'rgba(139, 92, 246, 0.12)', color: 'var(--accent-purple)', padding: '2px 8px', borderRadius: '10px', fontWeight: 600 }}>
            {options.length} {typeName} options
          </span>
        )}
      </div>

      {/* 1. Entity Selection Dropdown */}
      {options.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Selected {typeName.toUpperCase()}:
          </label>
          <select
            style={{
              width: '100%',
              padding: '9px 12px',
              borderRadius: '8px',
              background: 'var(--input-bg)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              fontSize: '13.5px',
              cursor: 'pointer',
              fontWeight: 500
            }}
            value={selectedEntity}
            onChange={(e) => {
              setSelectedEntity(e.target.value);
              setIsSubmitted(false);
            }}
          >
            {options.map((opt) => (
              <option key={opt.id} value={opt.label}>
                {opt.label} (ID: {opt.id})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 2. Intent Action Selection Chips */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Choose Analytical Intent:
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {[
            { id: 'pending_complaints', label: '📋 Pending Complaints' },
            { id: 'sla_breaches', label: '⏱️ SLA Breaches' },
            { id: 'officer_performance', label: '👤 Officer Workload' },
            { id: 'category_breakdown', label: '📊 Category Breakdown' }
          ].map((act) => {
            const isSelected = intentAction === act.id;
            return (
              <button
                key={act.id}
                type="button"
                onClick={() => {
                  setIntentAction(act.id);
                  setIsSubmitted(false);
                }}
                style={{
                  background: isSelected ? 'rgba(139, 92, 246, 0.2)' : 'var(--bg-card)',
                  border: isSelected ? '1px solid var(--accent-purple)' : '1px solid var(--border-color)',
                  color: isSelected ? 'var(--accent-purple)' : 'var(--text-primary)',
                  borderRadius: '20px',
                  padding: '6px 14px',
                  fontSize: '12px',
                  fontWeight: isSelected ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {act.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Query Preview & Submit Button Row */}
      <div style={{
        marginTop: '4px',
        padding: '12px 14px',
        borderRadius: '8px',
        background: 'rgba(0, 0, 0, 0.2)',
        border: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1, minWidth: '220px' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
            CONFIRM QUERY TO SEND:
          </span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-blue)', fontStyle: 'italic' }}>
            "{getIntentQuery()}"
          </span>
        </div>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitted || !selectedEntity}
          style={{
            background: isSubmitted
              ? '#10b981'
              : 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            padding: '9px 18px',
            fontSize: '13px',
            fontWeight: 700,
            cursor: isSubmitted ? 'default' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: isSubmitted ? 'none' : '0 4px 12px rgba(139, 92, 246, 0.35)',
            transition: 'all 0.2s ease',
            opacity: (!selectedEntity || isSubmitted) ? 0.8 : 1
          }}
        >
          {isSubmitted ? (
            <>
              <CheckCircle2 size={16} /> Submitted ✓
            </>
          ) : (
            <>
              <Send size={16} /> Submit Query
            </>
          )}
        </button>
      </div>
    </div>
  );
};
