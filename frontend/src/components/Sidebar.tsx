import React, { useState } from 'react';
import { MessageSquarePlus, Trash2, Edit2, Check, X, Search, Sparkles, Database, ChevronLeft, ChevronRight, Zap } from 'lucide-react';
import { ChatSessionDetailResponse } from '../types';

interface SidebarProps {
  sessions: ChatSessionDetailResponse[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  isOpen: boolean;
  onToggleSidebar: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen,
  onToggleSidebar
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredSessions = sessions.filter(s =>
    s.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <aside style={{
      width: isOpen ? '280px' : '0px',
      minWidth: isOpen ? '280px' : '0px',
      height: '100vh',
      background: 'rgba(15, 23, 42, 0.95)',
      backdropFilter: 'blur(20px)',
      borderRight: isOpen ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
      display: 'flex',
      flexDirection: 'column',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      overflow: 'hidden',
      position: 'relative',
      zIndex: 40
    }}>
      {isOpen && (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px' }}>
          {/* Header & New Chat Button */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
                padding: '6px',
                borderRadius: '8px',
                display: 'flex'
              }}>
                <Sparkles size={16} color="#ffffff" />
              </div>
              <span style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
                PMC AI Assistant
              </span>
            </div>

            <button
              onClick={onToggleSidebar}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: 'none',
                borderRadius: '6px',
                padding: '6px',
                color: '#94a3b8',
                cursor: 'pointer',
                display: 'flex'
              }}
              title="Close Sidebar"
            >
              <ChevronLeft size={18} />
            </button>
          </div>

          <button
            onClick={onNewChat}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              padding: '12px 16px',
              background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
              border: 'none',
              borderRadius: '10px',
              color: '#ffffff',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(56, 189, 248, 0.25)',
              transition: 'all 0.2s ease',
              marginBottom: '16px'
            }}
          >
            <MessageSquarePlus size={18} />
            <span>+ New Chat Thread</span>
          </button>

          {/* Search Box */}
          <div style={{
            position: 'relative',
            marginBottom: '16px'
          }}>
            <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search chat history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 32px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </div>

          {/* Sessions List */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            paddingRight: '4px'
          }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px', paddingLeft: '4px' }}>
              Recent Conversation Threads
            </div>

            {filteredSessions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 12px', color: '#64748b', fontSize: '13px' }}>
                No chat history found. Click "+ New Chat Thread" to start.
              </div>
            ) : (
              filteredSessions.map((session) => {
                const isActive = session.id === activeSessionId;
                return (
                  <div
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      background: isActive ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                      border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}

                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                      {session.mode === 'agent' ? (
                        <Sparkles size={14} color={isActive ? '#c084fc' : '#94a3b8'} />
                      ) : (
                        <Zap size={14} color={isActive ? '#38bdf8' : '#94a3b8'} />
                      )}
                      <span style={{
                        fontSize: '13px',
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? '#f8fafc' : '#cbd5e1',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {session.title}
                      </span>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        borderRadius: '4px'
                      }}
                      title="Delete thread"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Info */}
          <div style={{
            paddingTop: '12px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#64748b',
            fontSize: '12px'
          }}>
            <Database size={14} />
            <span>PostgreSQL Metadata DB Connected</span>
          </div>
        </div>
      )}
    </aside>
  );
};
