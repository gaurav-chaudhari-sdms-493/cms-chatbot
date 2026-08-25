import React from 'react';
import { QueryExecutionResult } from '../types';

interface ResultTableProps {
  result: QueryExecutionResult;
}

export const ResultTable: React.FC<ResultTableProps> = ({ result }) => {
  if (result.status === 'ERROR') {
    return (
      <div className="glass-panel" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.05)' }}>
        <h3 style={{ color: '#f87171', fontSize: '16px' }}>⚠️ Query Execution Error</h3>
        <p style={{ color: '#fca5a5', marginTop: '6px' }}>{result.error}</p>
      </div>
    );
  }

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
            Query Results ({result.total_rows} Rows)
          </h3>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            Executed Template: {result.template_id}
          </span>
        </div>
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontSize: '12px', fontWeight: 600, padding: '6px 12px', borderRadius: '8px' }}>
          ⚡ Executed in {result.execution_time_ms} ms
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              {result.columns.map((col) => (
                <th key={col}>{col.replace('_', ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.data.length === 0 ? (
              <tr>
                <td colSpan={result.columns.length} style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                  No matching records found in PMC database.
                </td>
              </tr>
            ) : (
              result.data.map((row, idx) => (
                <tr key={idx}>
                  {result.columns.map((col) => (
                    <td key={col}>{row[col] !== null ? String(row[col]) : 'NULL'}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
