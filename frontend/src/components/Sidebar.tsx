import React, { useState, useRef, useEffect } from 'react';
import { Edit3, Search, MoreHorizontal, Pin, Edit2, Trash2, PanelLeftClose, PanelLeft, Settings, Check, X, MessageSquare, Download } from 'lucide-react';
import { ChatSessionDetailResponse } from '../types';

interface SidebarProps {
  sessions: ChatSessionDetailResponse[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  isOpen: boolean;
  onToggleSidebar: () => void;
  onOpenSettings?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen,
  onToggleSidebar,
  onOpenSettings
}) => {
  const [showSearch, setShowSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isMobile, setIsMobile] = useState<boolean>(() => typeof window !== 'undefined' && window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const [pinnedIds, setPinnedIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('stark_ai_pinned_chats');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const [customTitles, setCustomTitles] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem('stark_ai_custom_titles');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const menuRef = useRef<HTMLDivElement>(null);

  // Save pinned chats to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('stark_ai_pinned_chats', JSON.stringify(pinnedIds));
    } catch (err) {
      console.error('Failed to save pinned chats:', err);
    }
  }, [pinnedIds]);

  // Save custom titles to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('stark_ai_custom_titles', JSON.stringify(customTitles));
    } catch (err) {
      console.error('Failed to save custom titles:', err);
    }
  }, [customTitles]);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpenId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const togglePin = (id: string) => {
    setPinnedIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
    setMenuOpenId(null);
  };

  const startRename = (session: ChatSessionDetailResponse) => {
    setEditingId(session.id);
    setEditTitle(customTitles[session.id] || session.title);
    setMenuOpenId(null);
  };

  const saveRename = (id: string) => {
    if (editTitle.trim()) {
      setCustomTitles((prev) => ({ ...prev, [id]: editTitle.trim() }));
    }
    setEditingId(null);
  };

  const handleExportChat = (session: ChatSessionDetailResponse) => {
    const title = customTitles[session.id] || session.title;
    let exportText = `# PMC Analytics Chat Export: ${title}\nSession ID: ${session.id}\nExported At: ${new Date().toLocaleString()}\n\n---\n\n`;

    if (session.messages && session.messages.length > 0) {
      session.messages.forEach((m) => {
        exportText += `### ${m.sender === 'user' ? '👤 PMC Officer' : '⚡ PMC Analytics AI Assistant'}\n${m.content}\n\n`;
      });
    } else {
      exportText += `(No chat messages in this session)\n`;
    }

    const blob = new Blob([exportText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pmc-chat-export-${session.id.slice(0, 8)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setMenuOpenId(null);
  };

  const filteredSessions = sessions.filter((s) => {
    const title = customTitles[s.id] || s.title;
    return title.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const pinnedSessions = filteredSessions.filter((s) => pinnedIds.includes(s.id));
  const recentSessions = filteredSessions.filter((s) => !pinnedIds.includes(s.id));

  // If mobile and closed, return null so mobile viewport is 100% clean
  if (isMobile && !isOpen) {
    return null;
  }

  // Collapsed Narrow Icon Rail View (Desktop Only)
  if (!isOpen) {
    return (
      <aside style={{
        width: '64px',
        minWidth: '64px',
        height: '100vh',
        background: 'var(--bg-sidebar)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 0',
        zIndex: 40,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
      }}>
        {/* Top Rail Action Icons */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
          {/* Expand Sidebar Button */}
          <button
            onClick={onToggleSidebar}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Expand Sidebar"
          >
            <PanelLeft size={20} />
          </button>

          {/* New Chat Icon Button */}
          <button
            onClick={onNewChat}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="New Chat"
          >
            <Edit3 size={20} />
          </button>

          {/* Search Icon Button */}
          <button
            onClick={() => {
              onToggleSidebar();
              setShowSearch(true);
            }}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Search Chats"
          >
            <Search size={20} />
          </button>

          {/* Pinned Chats Icon Button */}
          <button
            onClick={onToggleSidebar}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Pinned Chats"
          >
            <Pin size={20} />
          </button>

          {/* Messages Icon Button */}
          <button
            onClick={onToggleSidebar}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Recent Chats"
          >
            <MessageSquare size={20} />
          </button>
        </div>

        {/* Bottom Profile Avatar Item */}
        <button
          onClick={onOpenSettings}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Profile & Settings"
        >
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #f97316, #ea580c)',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            GC
          </div>
        </button>
      </aside>
    );
  }

  // Expanded Sidebar View (Fixed Overlay on Mobile, Inline on Desktop)
  return (
    <>
      {/* Mobile Dark Overlay Backdrop */}
      {isMobile && isOpen && (
        <div
          onClick={onToggleSidebar}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)',
            zIndex: 90
          }}
        />
      )}

      <aside style={{
        width: isMobile ? '280px' : '260px',
        minWidth: isMobile ? '280px' : '260px',
        height: '100vh',
        background: 'var(--bg-sidebar)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
        position: isMobile ? 'fixed' : 'relative',
        left: isMobile ? 0 : undefined,
        top: isMobile ? 0 : undefined,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '12px 14px' }}>

          {/* Header Bar: Title on Left, Search & Collapse icons on Right */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 6px 12px 6px'
          }}>
            <h2 style={{
              fontSize: '18px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.02em'
            }}>
              Stark AI
            </h2>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={() => setShowSearch(!showSearch)}
                style={{
                  background: showSearch ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Search Chats"
              >
                <Search size={18} />
              </button>

              <button
                onClick={onToggleSidebar}
                style={{
                  background: 'transparent',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Collapse Sidebar"
              >
                <PanelLeftClose size={18} />
              </button>
            </div>
          </div>

          {/* New Chat Button Item */}
          <button
            onClick={() => {
              onNewChat();
              if (isMobile) onToggleSidebar();
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 12px',
              background: 'transparent',
              border: 'none',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'background 0.2s ease',
              marginBottom: '12px'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <Edit3 size={18} color="var(--text-primary)" />
            <span>New chat</span>
          </button>

          {/* Search Box (Collapsible) */}
          {showSearch && (
            <div style={{ marginBottom: '12px' }}>
              <input
                type="text"
                placeholder="Search chats..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                autoFocus
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  outline: 'none'
                }}
              />
            </div>
          )}

          {/* Main Sessions List */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            paddingRight: '2px'
          }}>

            {/* Pinned Section */}
            {pinnedSessions.length > 0 && (
              <div>
                <div style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  padding: '4px 8px 6px 8px'
                }}>
                  Pinned
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {pinnedSessions.map((session) => renderSessionRow(session))}
                </div>
              </div>
            )}

            {/* Recents Section */}
            <div>
              <div style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                padding: '4px 8px 6px 8px'
              }}>
                Recents
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {recentSessions.length === 0 ? (
                  <div style={{ padding: '12px 8px', fontSize: '13px', color: 'var(--text-muted)' }}>
                    No recent chats
                  </div>
                ) : (
                  recentSessions.map((session) => renderSessionRow(session))
                )}
              </div>
            </div>

          </div>

          {/* Footer User Avatar Item with Settings Icon on Right */}
          <div style={{
            paddingTop: '12px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 8px 4px 8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #f97316, #ea580c)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                GC
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                  Gaurav Chaudhari
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  PMC Officer
                </span>
              </div>
            </div>

            {/* ⚙️ Settings gear icon button on the right side of profile */}
            {onOpenSettings && (
              <button
                onClick={() => {
                  onOpenSettings();
                  if (isMobile) onToggleSidebar();
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background 0.2s ease'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                title="Settings"
              >
                <Settings size={18} />
              </button>
            )}
          </div>

        </div>
      </aside>
    </>
  );

  function renderSessionRow(session: ChatSessionDetailResponse) {
    const isActive = session.id === activeSessionId;
    const isHovered = hoveredId === session.id;
    const isMenuOpen = menuOpenId === session.id;
    const isEditing = editingId === session.id;
    const title = customTitles[session.id] || session.title;
    const isPinned = pinnedIds.includes(session.id);

    return (
      <div
        key={session.id}
        onMouseEnter={() => setHoveredId(session.id)}
        onMouseLeave={() => setHoveredId(null)}
        onClick={() => {
          if (!isEditing) {
            onSelectSession(session.id);
            if (isMobile) onToggleSidebar();
          }
        }}
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 10px',
          borderRadius: '8px',
          background: isActive
            ? 'rgba(0, 0, 0, 0.08)'
            : isHovered
              ? 'rgba(0, 0, 0, 0.04)'
              : 'transparent',
          cursor: 'pointer',
          transition: 'all 0.15s ease'
        }}
      >
        {isEditing ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', width: '100%' }} onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') saveRename(session.id);
                if (e.key === 'Escape') setEditingId(null);
              }}
              autoFocus
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: '13px',
                borderRadius: '4px',
                border: '1px solid var(--accent-blue)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            />
            <button
              onClick={() => saveRename(session.id)}
              style={{ background: 'transparent', border: 'none', color: '#34d399', cursor: 'pointer', padding: '2px' }}
            >
              <Check size={14} />
            </button>
            <button
              onClick={() => setEditingId(null)}
              style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '2px' }}
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
              <span style={{
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {title}
              </span>
            </div>

            {/* Hover 3-Dots Button */}
            {(isHovered || isMenuOpen || isMobile) && (
              <div style={{ position: 'relative' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpenId(isMenuOpen ? null : session.id);
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    padding: '2px 4px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="Options"
                >
                  <MoreHorizontal size={16} />
                </button>

                {/* 3-Dots Dropdown Menu (Pin, Rename, Delete) */}
                {isMenuOpen && (
                  <div
                    ref={menuRef}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: '24px',
                      zIndex: 60,
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '10px',
                      boxShadow: '0 10px 25px -5px rgba(0,0,0,0.25)',
                      padding: '6px',
                      minWidth: '130px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px'
                    }}
                  >
                    <button
                      onClick={() => togglePin(session.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 10px',
                        fontSize: '13px',
                        color: 'var(--text-primary)',
                        background: 'transparent',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        textAlign: 'left'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <Pin size={14} color="var(--accent-blue)" />
                      <span>{isPinned ? 'Unpin' : 'Pin'}</span>
                    </button>

                    <button
                      onClick={() => handleExportChat(session)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 10px',
                        fontSize: '13px',
                        color: 'var(--text-primary)',
                        background: 'transparent',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        textAlign: 'left'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <Download size={14} color="var(--accent-blue)" />
                      <span>Export Chat</span>
                    </button>

                    <button
                      onClick={() => startRename(session)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 10px',
                        fontSize: '13px',
                        color: 'var(--text-primary)',
                        background: 'transparent',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        textAlign: 'left'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <Edit2 size={14} color="var(--accent-purple)" />
                      <span>Rename</span>
                    </button>

                    <button
                      onClick={() => {
                        onDeleteSession(session.id);
                        setMenuOpenId(null);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 10px',
                        fontSize: '13px',
                        color: '#f87171',
                        background: 'transparent',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        textAlign: 'left'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <Trash2 size={14} color="#f87171" />
                      <span>Delete</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    );
  }
};
