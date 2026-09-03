import React, { useState, useEffect } from 'react';
import { MessageSquare, Maximize2, Minimize2, Minus, X, Trash2, Sparkles, Sun, Moon, RefreshCw, BarChart2, TrendingUp, AlertCircle } from 'lucide-react';
import { ChatStream } from './ChatStream';
import { QueryInput, QueryMode } from './QueryInput';
import { ChatMessageResponse, ChatSessionDetailResponse } from '../types';
import {
  fetchChatSessions,
  createChatSession,
  fetchChatSessionById,
  deleteChatSession,
  sendChatMessage
} from '../services/api';

interface ChatWidgetProps {
  initialEmbed?: boolean;
  theme?: 'dark' | 'light';
  onThemeToggle?: () => void;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({
  initialEmbed = false,
  theme = 'light',
  onThemeToggle
}) => {
  const [isOpen, setIsOpen] = useState(initialEmbed);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showTooltip, setShowTooltip] = useState(true);

  // Chat Session States
  const [sessions, setSessions] = useState<ChatSessionDetailResponse[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeMessages, setActiveMessages] = useState<ChatMessageResponse[]>([]);
  const [queryMode, setQueryMode] = useState<QueryMode>('agent');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initial session load
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await fetchChatSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
        setActiveMessages(data[0].messages || []);
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const handleNewChat = async () => {
    try {
      const newSession = await createChatSession('Widget Chat', queryMode);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setActiveMessages([]);
      setErrorMsg(null);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to start new chat');
    }
  };

  const handleSearch = async (queryText: string, mode: QueryMode) => {
    setLoading(true);
    setErrorMsg(null);
    setShowTooltip(false);

    let tempMsgId = -Date.now();
    try {
      let currentId = activeSessionId;
      if (!currentId) {
        const newSession = await createChatSession(queryText.slice(0, 30), mode);
        setSessions((prev) => [newSession, ...prev]);
        currentId = newSession.id;
        setActiveSessionId(currentId);
      }

      if (!currentId) return;

      // Optimistic User Message
      const optimisticMsg: ChatMessageResponse = {
        id: tempMsgId,
        session_id: currentId,
        sender: 'user',
        content: queryText,
        sql_used: null,
        execution_time_ms: null,
        created_at: new Date().toISOString()
      };
      setActiveMessages((prev) => [...prev, optimisticMsg]);

      // API Call
      const chatResp = await sendChatMessage(currentId, queryText);

      // Replace optimistic message with canonical responses
      setActiveMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempMsgId);
        return [...filtered, chatResp.user_message, chatResp.agent_message];
      });

      loadSessions();
    } catch (err: any) {
      setActiveMessages((prev) => prev.filter((m) => m.id !== tempMsgId));
      setErrorMsg(err.message || 'Failed to process request.');
    } finally {
      setLoading(false);
    }
  };

  // Preset suggestion chips for quick clicks
  const quickSuggestions = [
    { label: '⚡ Pending Complaints', query: 'Show count of pending complaints by ward' },
    { label: '📈 2025 vs 2026 Trends', query: 'give me the comparison table for year 2025, and 2026... months wise' },
    { label: '📊 Complaints by Ward', query: 'Show a bar chart of total complaints registered by ward' }
  ];

  return (
    <>
      {/* 1. Floating Circular Launcher Badge at Bottom Right */}
      {!isOpen && !isMinimized && (
        <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999, display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Welcome Tooltip Bubble */}
          {showTooltip && (
            <div
              style={{
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--accent-blue)',
                padding: '10px 14px',
                borderRadius: '12px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                animation: 'pulse 2s infinite'
              }}
            >
              <Sparkles size={16} color="var(--accent-blue)" />
              <span>👋 Need PMC complaints or ward insights?</span>
              <button
                onClick={(e) => { e.stopPropagation(); setShowTooltip(false); }}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}
              >
                <X size={13} />
              </button>
            </div>
          )}

          {/* Floating Launcher Circle Button */}
          <button
            onClick={() => { setIsOpen(true); setIsMinimized(false); setShowTooltip(false); }}
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '30px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              color: '#ffffff',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 28px rgba(59, 130, 246, 0.4)',
              transition: 'transform 0.2s ease'
            }}
            title="Open PMC Assistant"
          >
            <MessageSquare size={26} />
          </button>
        </div>
      )}

      {/* Minimized Docked Tab at Bottom Right */}
      {isMinimized && (
        <button
          onClick={() => { setIsOpen(true); setIsMinimized(false); }}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            background: 'var(--bg-card)',
            border: '1px solid var(--accent-blue)',
            color: 'var(--accent-blue)',
            padding: '10px 18px',
            borderRadius: '24px',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.15)',
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <MessageSquare size={18} />
          <span>PMC Assistant (Click to restore)</span>
        </button>
      )}

      {/* 2. Main Chatbot Drawer / Popup / Fullscreen Container */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            zIndex: 10000,
            ...(isFullscreen
              ? { top: 0, left: 0, right: 0, bottom: 0, width: '100vw', height: '100vh', borderRadius: 0 }
              : { bottom: '24px', right: '24px', width: '440px', height: '700px', maxHeight: 'calc(100vh - 48px)', borderRadius: '16px' }),
            background: 'var(--bg-dark)',
            border: '1px solid var(--border-color)',
            boxShadow: '0 16px 48px rgba(0, 0, 0, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
          }}
        >
          {/* Widget Header Bar */}
          <div
            style={{
              padding: '12px 16px',
              background: 'var(--bg-card-hover)',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff'
                }}
              >
                <Sparkles size={18} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  PMC Assistant
                </h3>
              </div>
            </div>

            {/* Window Action Control Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {/* Reset Session Button */}
              <button
                onClick={handleNewChat}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="New Chat Session"
              >
                <RefreshCw size={15} />
              </button>

              {/* Fullscreen / Compact Mode Switcher */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
              >
                {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
              </button>

              {/* Minimize Button */}
              <button
                onClick={() => { setIsOpen(false); setIsMinimized(true); }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Minimize Widget"
              >
                <Minus size={16} />
              </button>

              {/* Close Button */}
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Close Assistant"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Chat Messages Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
            {errorMsg && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  marginBottom: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <AlertCircle size={14} />
                <span>{errorMsg}</span>
              </div>
            )}

            <ChatStream
              messages={activeMessages}
              loading={loading}
              questionText=""
              onSelectExample={(q) => handleSearch(q, queryMode)}
            />
          </div>

          {/* Sticky Bottom Input Bar */}
          <div style={{ borderTop: '1px solid var(--border-color)', background: 'var(--bg-card)' }}>
            <QueryInput
              onSearch={handleSearch}
              loading={loading}
              activeMode={queryMode}
              onModeChange={(m) => setQueryMode(m)}
            />
          </div>
        </div>
      )}
    </>
  );
};
