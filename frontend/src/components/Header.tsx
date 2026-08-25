import React from 'react';

interface HeaderProps {
  health: { status: string; database?: { department_master_rows?: number } } | null;
  activeTab: 'query' | 'developer';
  onTabChange: (tab: 'query' | 'developer') => void;
}

export const Header: React.FC<HeaderProps> = ({ health, activeTab, onTabChange }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
      <div>
        <h1 className="brand-title">PMC Officer Query System</h1>
        <p className="brand-subtitle">
          Controlled Natural Language Analytics Interface — Pune Municipal Corporation
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.6)', padding: '4px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <button
            onClick={() => onTabChange('query')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              transition: 'all 0.2s ease',
              background: activeTab === 'query' ? 'linear-gradient(135deg, #3b82f6, #2563eb)' : 'transparent',
              color: activeTab === 'query' ? '#ffffff' : '#94a3b8',
              boxShadow: activeTab === 'query' ? '0 4px 12px rgba(37, 99, 235, 0.4)' : 'none'
            }}
          >
            🔍 Officer Query
          </button>

          <button
            onClick={() => onTabChange('developer')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              transition: 'all 0.2s ease',
              background: activeTab === 'developer' ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' : 'transparent',
              color: activeTab === 'developer' ? '#ffffff' : '#94a3b8',
              boxShadow: activeTab === 'developer' ? '0 4px 12px rgba(124, 58, 237, 0.4)' : 'none'
            }}
          >
            🛠️ Developer Studio
          </button>
        </div>

        <div className="status-badge" style={{ borderColor: isHealthy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)', color: isHealthy ? '#34d399' : '#f87171' }}>
          <span className="status-dot" style={{ backgroundColor: isHealthy ? '#10b981' : '#ef4444', boxShadow: isHealthy ? '0 0 8px #10b981' : '0 0 8px #ef4444' }}></span>
          {isHealthy ? `Backend Healthy (${health?.database?.department_master_rows || 166} Depts)` : 'Connecting to Backend...'}
        </div>
      </div>
    </header>
  );
};
