import React from 'react';
import { X, Moon, Sun, Zap, Sparkles, LayoutDashboard, Code, Sliders } from 'lucide-react';
import { QueryMode } from './QueryInput';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: 'query' | 'developer';
  onTabChange: (tab: 'query' | 'developer') => void;
  queryMode: QueryMode;
  onModeChange: (mode: QueryMode) => void;
  theme: 'dark' | 'light';
  onThemeChange: (theme: 'dark' | 'light') => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  queryMode,
  onModeChange,
  theme,
  onThemeChange
}) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      background: 'rgba(0, 0, 0, 0.65)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }} onClick={onClose}>
      <div style={{
        width: '100%',
        maxWidth: '540px',
        background: 'var(--bg-card)',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color)',
        borderRadius: '20px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden',
        animation: 'fadeIn 0.2s ease-out'
      }} onClick={(e) => e.stopPropagation()}>

        {/* Modal Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-color)',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={20} color="var(--accent-blue)" />
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Settings & Preferences
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>

          {/* Section 1: Navigation View */}
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px', display: 'block' }}>
              System Navigation View
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <button
                type="button"
                onClick={() => onTabChange('query')}
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: activeTab === 'query' ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  background: activeTab === 'query' ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-card)',
                  color: activeTab === 'query' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
              >
                <LayoutDashboard size={18} color={activeTab === 'query' ? '#38bdf8' : '#94a3b8'} />
                <span>🔍 Officer Query</span>
              </button>

              <button
                type="button"
                onClick={() => onTabChange('developer')}
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: activeTab === 'developer' ? '2px solid var(--accent-purple)' : '1px solid var(--border-color)',
                  background: activeTab === 'developer' ? 'rgba(139, 92, 246, 0.15)' : 'var(--bg-card)',
                  color: activeTab === 'developer' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
              >
                <Code size={18} color={activeTab === 'developer' ? '#c084fc' : '#94a3b8'} />
                <span>🛠️ Developer Studio</span>
              </button>
            </div>
          </div>

          {/* Section 2: Query Engine Mode */}
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px', display: 'block' }}>
              Query Execution Engine Mode
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                type="button"
                onClick={() => onModeChange('agent')}
                style={{
                  padding: '14px 16px',
                  borderRadius: '12px',
                  border: queryMode === 'agent' ? '2px solid #c084fc' : '1px solid var(--border-color)',
                  background: queryMode === 'agent' ? 'rgba(168, 85, 247, 0.15)' : 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Sparkles size={18} color="#c084fc" />
                  <div style={{ textAlign: 'left' }}>
                    <div>🧠 Stark AI Agent Mode ("Anything & Everything")</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 400 }}>
                      Autonomous NL2SQL agent with multi-turn memory & self-correction
                    </div>
                  </div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => onModeChange('template')}
                style={{
                  padding: '14px 16px',
                  borderRadius: '12px',
                  border: queryMode === 'template' ? '2px solid #38bdf8' : '1px solid var(--border-color)',
                  background: queryMode === 'template' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Zap size={18} color="#38bdf8" />
                  <div style={{ textAlign: 'left' }}>
                    <div>⚡ Structural Template Mode</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 400 }}>
                      Pre-approved canonical query templates with strict parameters
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Section 3: Appearance / Theme */}
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px', display: 'block' }}>
              Appearance Theme
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <button
                type="button"
                onClick={() => onThemeChange('dark')}
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: theme === 'dark' ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  background: theme === 'dark' ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-card)',
                  color: theme === 'dark' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
              >
                <Moon size={18} color={theme === 'dark' ? '#38bdf8' : '#94a3b8'} />
                <span>Dark Theme</span>
              </button>

              <button
                type="button"
                onClick={() => onThemeChange('light')}
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: theme === 'light' ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  background: theme === 'light' ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-card)',
                  color: theme === 'light' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
              >
                <Sun size={18} color={theme === 'light' ? '#f59e0b' : '#94a3b8'} />
                <span>Light Theme</span>
              </button>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-color)',
          background: 'rgba(0, 0, 0, 0.05)',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-indigo))',
              border: 'none',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
};
