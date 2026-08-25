import React from 'react';
import { TemplateSuggestion } from '../types';

interface SuggestionCardProps {
  suggestion: TemplateSuggestion;
  isSelected: boolean;
  onSelect: (suggestion: TemplateSuggestion) => void;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  suggestion,
  isSelected,
  onSelect
}) => {
  const matchPercentage = (suggestion.score * 100).toFixed(1);
  const detectedKeys = Object.keys(suggestion.detected_values);

  return (
    <div
      className={`card-suggestion ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(suggestion)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>
          {suggestion.template_id}
        </span>
        <span className="score-tag">{matchPercentage}% Match</span>
      </div>

      <h3 className="template-title">{suggestion.question_template}</h3>

      {detectedKeys.length > 0 && (
        <div style={{ marginTop: '10px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Detected Entities:</span>
          {detectedKeys.map((key) => {
            const val = suggestion.detected_values[key];
            return (
              <span key={key} className="detected-badge">
                ✓ {key}: {val.label} (ID: {val.id})
              </span>
            );
          })}
        </div>
      )}

      {suggestion.missing_placeholders.length > 0 && (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#f59e0b' }}>
          ⚠️ Needs value for: {suggestion.missing_placeholders.map((p) => p.placeholder_name).join(', ')}
        </div>
      )}
    </div>
  );
};
