import React, { useState, useEffect } from 'react';
import { PanelLeft } from 'lucide-react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatStream } from './components/ChatStream';
import { QueryInput, QueryMode } from './components/QueryInput';

import { SuggestionCard } from './components/SuggestionCard';
import { DynamicPlaceholderForm } from './components/DynamicPlaceholderForm';
import { ResultTable } from './components/ResultTable';
import { DeveloperStudio } from './components/DeveloperStudio';
import { SettingsModal } from './components/SettingsModal';
import { TemplateSuggestion, QueryExecutionResult, AgentQueryResponse, ChatSessionDetailResponse, ChatMessageResponse } from './types';
import {
    fetchSuggestions,
    executeQueryTemplate,
    fetchChatSessions,
    createChatSession,
    fetchChatSessionById,
    deleteChatSession,
    sendChatMessage
} from './services/api';

export const App: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'query' | 'developer'>('query');
    const [queryMode, setQueryMode] = useState<QueryMode>('agent');
    const [theme, setTheme] = useState<'dark' | 'light'>('light');
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    // Sidebar & Multi-Chat States
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [sessions, setSessions] = useState<ChatSessionDetailResponse[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeMessages, setActiveMessages] = useState<ChatMessageResponse[]>([]);
    const [currentQuestionText, setCurrentQuestionText] = useState('');

    // Template Mode states
    const [suggestions, setSuggestions] = useState<TemplateSuggestion[]>([]);
    const [selectedSuggestion, setSelectedSuggestion] = useState<TemplateSuggestion | null>(null);
    const [executionResult, setExecutionResult] = useState<QueryExecutionResult | null>(null);

    // Standalone Agent Mode fallback state
    const [agentResult, setAgentResult] = useState<AgentQueryResponse | null>(null);

    const [loading, setLoading] = useState(false);
    const [executing, setExecuting] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    // Apply Theme to document root
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    // Initial load: Fetch health & chat sessions
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

    const handleSelectSession = async (sessionId: string) => {
        setActiveSessionId(sessionId);
        setAgentResult(null);
        setSuggestions([]);
        setSelectedSuggestion(null);
        setExecutionResult(null);
        setErrorMsg(null);

        try {
            const details = await fetchChatSessionById(sessionId);
            setActiveMessages(details.messages || []);
        } catch (err: any) {
            setErrorMsg(err.message || 'Failed to load session details.');
        }
    };

    const handleNewChat = async () => {
        try {
            const newSession = await createChatSession('New Chat', queryMode);
            setSessions((prev) => [newSession, ...prev]);
            setActiveSessionId(newSession.id);
            setActiveMessages([]);
            setAgentResult(null);
            setSuggestions([]);
            setSelectedSuggestion(null);
            setExecutionResult(null);
            setErrorMsg(null);
        } catch (err: any) {
            setErrorMsg(err.message || 'Failed to create new chat.');
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        try {
            await deleteChatSession(sessionId);
            setSessions((prev) => prev.filter((s) => s.id !== sessionId));
            if (activeSessionId === sessionId) {
                const remaining = sessions.filter((s) => s.id !== sessionId);
                if (remaining.length > 0) {
                    handleSelectSession(remaining[0].id);
                } else {
                    setActiveSessionId(null);
                    setActiveMessages([]);
                }
            }
        } catch (err: any) {
            setErrorMsg(err.message || 'Failed to delete chat session.');
        }
    };

    const handleSearch = async (queryText: string, mode: QueryMode) => {
        setLoading(true);
        setErrorMsg(null);
        setSelectedSuggestion(null);
        setExecutionResult(null);
        setCurrentQuestionText(queryText);

        if (mode === 'template') {
            try {
                const response = await fetchSuggestions(queryText);
                setSuggestions(response.suggestions);
                if (response.suggestions.length > 0) {
                    setSelectedSuggestion(response.suggestions[0]);
                }
            } catch (err: any) {
                setErrorMsg(err.message || 'Failed to fetch template suggestions.');
            } finally {
                setLoading(false);
            }
        } else {
            // Stark AI Agent Mode (Multi-Turn Chat History Persistence)
            let tempMsgId = -Date.now();
            try {
                let currentId = activeSessionId;
                if (!currentId) {
                    const newSession = await createChatSession(queryText.slice(0, 30), 'agent');
                    setSessions((prev) => [newSession, ...prev]);
                    currentId = newSession.id;
                    setActiveSessionId(currentId);
                }

                if (!currentId) return;

                // Optimistically append user message to chat immediately
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

                // Send message to persistent chat session API
                const chatResp = await sendChatMessage(currentId, queryText);

                // Replace temporary optimistic message with canonical user & agent response messages
                setActiveMessages((prev) => {
                    const filtered = prev.filter((m) => m.id !== tempMsgId);
                    return [...filtered, chatResp.user_message, chatResp.agent_message];
                });

                // Refresh sessions sidebar list
                loadSessions();
            } catch (err: any) {
                // Remove optimistic message if error occurs
                setActiveMessages((prev) => prev.filter((m) => m.id !== tempMsgId));
                setErrorMsg(err.message || 'Stark AI Agent execution failed.');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleExecute = async (parameters: Record<string, any>) => {
        if (!selectedSuggestion) return;
        setExecuting(true);
        setErrorMsg(null);

        try {
            const result = await executeQueryTemplate(selectedSuggestion.template_id, parameters);
            setExecutionResult(result);
        } catch (err: any) {
            setErrorMsg(err.message || 'Failed to execute query template.');
        } finally {
            setExecuting(false);
        }
    };

    return (
        <div style={{ display: 'flex', width: '100vw', height: '100vh', background: 'var(--bg-dark)', overflow: 'hidden' }}>
            {/* Settings Modal */}
            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                activeTab={activeTab}
                onTabChange={(tab) => {
                    setActiveTab(tab);
                    setIsSettingsOpen(false);
                }}
                queryMode={queryMode}
                onModeChange={(m) => {
                    setQueryMode(m);
                    setSuggestions([]);
                    setSelectedSuggestion(null);
                    setExecutionResult(null);
                    setAgentResult(null);
                    setErrorMsg(null);
                }}
                theme={theme}
                onThemeChange={(t) => setTheme(t)}
            />

            {/* ChatGPT-style Sidebar with Collapsed Narrow Rail */}
            <Sidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
                isOpen={isSidebarOpen}
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                onOpenSettings={() => setIsSettingsOpen(true)}
            />

            {/* Main Container */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, height: '100vh', position: 'relative' }}>
                {/* Floating Collapsed Sidebar Expand Button */}
                {!isSidebarOpen && (
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        style={{
                            position: 'absolute',
                            top: '16px',
                            left: '16px',
                            zIndex: 30,
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '10px',
                            padding: '8px 10px',
                            color: 'var(--text-primary)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                        }}
                        title="Open Sidebar"
                    >
                        <PanelLeft size={18} />
                    </button>
                )}

                {/* Scrollable Content Body */}
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>


                    <main style={{ flex: 1, maxWidth: '1100px', margin: '0 auto', width: '100%', padding: '24px 24px 0 24px' }}>
                        {activeTab === 'developer' ? (
                            <DeveloperStudio />
                        ) : (
                            <>
                                {errorMsg && (
                                    <div className="glass-panel" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.05)', color: '#f87171', marginTop: '16px' }}>
                                        ⚠️ {errorMsg}
                                    </div>
                                )}

                                {/* Template Mode Output */}
                                {queryMode === 'template' && (
                                    <>
                                        {suggestions.length > 0 && (
                                            <div className="glass-panel" style={{ marginTop: '20px' }}>
                                                <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                                                    Top Matching Approved Query Templates
                                                </h2>
                                                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                                    Select a template to view detected entity values or resolve missing placeholders.
                                                </p>

                                                <div className="suggestions-grid">
                                                    {suggestions.map((s) => (
                                                        <SuggestionCard
                                                            key={s.template_id}
                                                            suggestion={s}
                                                            isSelected={selectedSuggestion?.template_id === s.template_id}
                                                            onSelect={(item) => {
                                                                setSelectedSuggestion(item);
                                                                setExecutionResult(null);
                                                            }}
                                                        />
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {selectedSuggestion && (
                                            <DynamicPlaceholderForm
                                                suggestion={selectedSuggestion}
                                                onExecute={handleExecute}
                                                executing={executing}
                                            />
                                        )}

                                        {executionResult && <ResultTable result={executionResult} />}
                                    </>
                                )}

                                {/* Stark AI Agent Mode (Multi-Turn Chat Stream) */}
                                {queryMode === 'agent' && (
                                    <ChatStream
                                        messages={activeMessages}
                                        loading={loading}
                                        questionText={currentQuestionText}
                                        onSelectExample={(q) => handleSearch(q, queryMode)}
                                    />
                                )}
                            </>
                        )}
                    </main>
                </div>

                {/* Sticky Bottom Query Input Bar (Officer Query View Only) */}
                {activeTab === 'query' && (
                    <QueryInput
                        onSearch={handleSearch}
                        loading={loading}
                        activeMode={queryMode}
                        onModeChange={(mode) => setQueryMode(mode)}
                    />
                )}

            </div>
        </div>
    );
};

export default App;
