import React from 'react';
import { PanelLeft, Sun, Moon, Settings } from 'lucide-react';

interface HeaderProps {
  health: { status: string; database?: { department_master_rows?: number } } | null;
  activeTab: 'query' | 'developer';
  onTabChange: (tab: 'query' | 'developer') => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
  theme?: 'dark' | 'light';
  onThemeChange?: (theme: 'dark' | 'light') => void;
  onOpenSettings?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  activeTab,
  onTabChange,
  onToggleSidebar,
  isSidebarOpen,
  theme = 'light',
  onThemeChange,
  onOpenSettings
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="header" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',

      flexWrap: 'wrap',
      gap: '16px',
      padding: '16px 24px',
      background: 'var(--bg-card)',
      borderBottom: '1px solid var(--border-color)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            style={{
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px 10px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            title={isSidebarOpen ? 'Collapse Chat History Sidebar' : 'Open Chat History Sidebar'}
          >
            <PanelLeft size={20} color={isSidebarOpen ? 'var(--accent-blue)' : 'var(--text-secondary)'} />
          </button>
        )}
        <div>
          <h1 className="brand-title" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            PMC Officer Query System — Stark AI
          </h1>
          <p className="brand-subtitle" style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            Controlled Natural Language Analytics Interface — Pune Municipal Corporation
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', background: 'var(--bg-card-hover)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
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
              color: activeTab === 'query' ? '#ffffff' : 'var(--text-secondary)'
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
              color: activeTab === 'developer' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            🛠️ Developer Studio
          </button>
        </div>

        {/* Theme Switcher Button */}
        {onThemeChange && (
          <button
            onClick={() => onThemeChange(theme === 'light' ? 'dark' : 'light')}
            style={{
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '8px 12px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: 600,
              fontSize: '13px',
              transition: 'all 0.2s ease'
            }}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme === 'light' ? (
              <>
                <Moon size={16} color="#475569" />
                <span>Dark Mode</span>
              </>
            ) : (
              <>
                <Sun size={16} color="#f59e0b" />
                <span>Light Mode</span>
              </>
            )}
          </button>
        )}

        {/* Settings Button */}
        {onOpenSettings && (
          <button
            onClick={onOpenSettings}
            style={{
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '8px 10px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            title="Open System Settings"
          >
            <Settings size={18} />
          </button>
        )}
      </div>
    </header>
  );
};

