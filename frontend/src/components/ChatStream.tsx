import React, { useRef, useEffect } from 'react';
import { User, Sparkles, UserCheck, BarChart3, AlertTriangle, MapPin } from 'lucide-react';
import { ChatMessageResponse, AgentQueryResponse } from '../types';
import { MarkdownReport } from './MarkdownReport';
import { AnimatedProgress } from './AnimatedProgress';

interface Props {
    messages: ChatMessageResponse[];
    loading: boolean;
    questionText: string;
    onSelectExample?: (queryText: string) => void;
}

const WELCOME_CARDS = [
    {
        icon: UserCheck,
        color: '#8b5cf6',
        title: 'Officer Performance Report',
        description: 'Analyze workload, pending tasks & resolution rates for specific officers',
        prompt: 'performance report for SUSHIL CHANDRAKANT MOHITE'
    },
    {
        icon: BarChart3,
        color: '#3b82f6',
        title: 'Department Analytics',
        description: 'Inspect open complaints breakdown by workflow status & departments',
        prompt: 'Show open complaints breakdown by workflow status'
    },
    {
        icon: AlertTriangle,
        color: '#ef4444',
        title: 'SLA Breach Tracking',
        description: 'Identify wards & departments with highest SLA resolution delays',
        prompt: 'Which ward has the most SLA breaches in last 30 days?'
    },
    {
        icon: MapPin,
        color: '#10b981',
        title: 'Ward Complaint Trends',
        description: 'Track monthly complaint registration volumes across municipal wards',
        prompt: 'how many complaints registered in the last month for Baner?'
    }
];

export const ChatStream: React.FC<Props> = ({ messages, loading, questionText, onSelectExample }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    // Empty State / Welcome Screen for New Chat
    if (messages.length === 0 && !loading) {
        return (
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '60vh',
                padding: '32px 16px',
                textAlign: 'center',
                maxWidth: '850px',
                margin: '0 auto'
            }}>
                {/* Glowing Logo Badge */}
                <div style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '16px',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 8px 24px -4px rgba(139, 92, 246, 0.4)',
                    marginBottom: '20px'
                }}>
                    <Sparkles size={28} color="#ffffff" />
                </div>

                {/* Welcome Greeting Header */}
                <h1 style={{
                    fontSize: '28px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.02em',
                    marginBottom: '8px'
                }}>
                    What would you like to analyze today?
                </h1>
                <p style={{
                    fontSize: '14px',
                    color: 'var(--text-secondary)',
                    maxWidth: '560px',
                    lineHeight: 1.6,
                    marginBottom: '36px'
                }}>
                    Stark AI provides autonomous natural language analytics over PMC municipal databases, officer SLA performance & department grievance records.
                </p>

                {/* 4 Interactive Quick Starter Cards */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                    gap: '14px',
                    width: '100%'
                }}>
                    {WELCOME_CARDS.map((card, idx) => {
                        const Icon = card.icon;
                        return (
                            <div
                                key={idx}
                                onClick={() => onSelectExample && onSelectExample(card.prompt)}
                                style={{
                                    background: 'var(--bg-card)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '14px',
                                    padding: '18px 20px',
                                    textAlign: 'left',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '8px'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = card.color;
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = `0 8px 20px -4px ${card.color}22`;
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = 'var(--border-color)';
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = 'none';
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <div style={{
                                        padding: '8px',
                                        borderRadius: '8px',
                                        background: `${card.color}15`,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center'
                                    }}>
                                        <Icon size={18} color={card.color} />
                                    </div>
                                    <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                                        {card.title}
                                    </h3>
                                </div>
                                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                                    {card.description}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '16px 0' }}>
            {messages.map((msg) => {
                if (msg.sender === 'user') {
                    return (
                        <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                            <div style={{
                                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%)',
                                border: '1px solid rgba(168, 85, 247, 0.4)',
                                borderRadius: '16px 16px 4px 16px',
                                padding: '14px 20px',
                                maxWidth: '75%',
                                color: 'var(--text-primary)',
                                fontSize: '15px',
                                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                            }}>
                                {msg.content}
                            </div>
                            <div style={{
                                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                                width: '36px',
                                height: '36px',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0
                            }}>
                                <User size={18} color="#ffffff" />
                            </div>
                        </div>
                    );
                } else {
                    // Agent message
                    const agentResponse: AgentQueryResponse = {
                        question: questionText || 'Query Result',
                        markdown_report: msg.content,
                        sql_used: msg.sql_used || '',
                        template_id: msg.template_id,
                        candidate_templates: msg.candidate_templates,
                        execution_time_ms: msg.execution_time_ms || 0,
                        retry_count: 0,
                        status: 'SUCCESS'
                    };
                    return (
                        <div key={msg.id} style={{ width: '100%' }}>
                            <MarkdownReport data={agentResponse} onSelectOption={onSelectExample} />
                        </div>
                    );
                }
            })}

            {/* Animated Multi-Stage Progress Bar when waiting for LLM */}
            {loading && <AnimatedProgress />}

            <div ref={bottomRef} />
        </div>
    );
};
