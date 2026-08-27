import React, { useState, useEffect } from 'react';
import { Database, Sparkles, Cpu, FileText } from 'lucide-react';

const STAGES = [
  {
    icon: Database,
    label: 'Scanning PMC Database & Metadata',
    subtext: 'Exploring department master schemas and column definitions...',
    color: '#38bdf8'
  },
  {
    icon: Sparkles,
    label: 'Stark AI is thinking & reasoning',
    subtext: 'Understanding query intent and mapping canonical entities...',
    color: '#c084fc'
  },
  {
    icon: Cpu,
    label: 'Executing query & verifying schema',
    subtext: 'Running safe read-only SQL query against PostgreSQL DB...',
    color: '#818cf8'
  },
  {
    icon: FileText,
    label: 'Generating response report',
    subtext: 'Formatting data tables, metrics, and summary insights...',
    color: '#34d399'
  }
];

export const AnimatedProgress: React.FC = () => {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStageIndex((prevStage) => {
        if (prevStage < STAGES.length - 1) {
          return prevStage + 1;
        }
        return prevStage;
      });
    }, 1400);

    return () => clearInterval(timer);
  }, []);

  const currentStage = STAGES[stageIndex];
  const CurrentIcon = currentStage.icon;

  return (
    <div style={{
      background: 'var(--bg-card)',
      backdropFilter: 'blur(16px)',
      border: '1px solid var(--border-color)',
      borderRadius: '16px',
      padding: '20px 24px',
      marginTop: '12px',
      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15)',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px'
    }}>
      {/* Active Stage Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          background: `rgba(${stageIndex === 0 ? '56, 189, 248' : stageIndex === 1 ? '192, 132, 252' : stageIndex === 2 ? '129, 140, 248' : '52, 211, 153'}, 0.15)`,
          padding: '10px',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          animation: 'pulseGlowIcon 1.8s infinite ease-in-out'
        }}>
          <CurrentIcon size={22} color={currentStage.color} />
        </div>

        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: '15px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center'
          }}>
            <span>{currentStage.label}</span>
            <span className="bouncing-dots" style={{ color: currentStage.color }}>
              <span className="bouncing-dot" />
              <span className="bouncing-dot" />
              <span className="bouncing-dot" />
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {currentStage.subtext}
          </div>
        </div>
      </div>

      {/* Dynamic Indeterminate Animated Waiting Bar */}
      <div className="waiting-bar-container">
        <div className="waiting-bar-active" />
      </div>
    </div>
  );
};
