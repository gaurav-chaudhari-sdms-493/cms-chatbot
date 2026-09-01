import React, { useState, useEffect } from 'react';
import { TemplateSuggestion, PlaceholderMetadata } from '../types';
import { fetchReferenceOptions } from '../services/api';

interface DynamicPlaceholderFormProps {
  suggestion: TemplateSuggestion;
  onExecute: (params: Record<string, any>) => void;
  executing: boolean;
}

export const DynamicPlaceholderForm: React.FC<DynamicPlaceholderFormProps> = ({
  suggestion,
  onExecute,
  executing
}) => {
  const [paramState, setParamState] = useState<Record<string, any>>({});
  const [referenceOptions, setReferenceOptions] = useState<Record<string, { id: any; label: string }[]>>({});
  const [loadingOptions, setLoadingOptions] = useState<Record<string, boolean>>({});

  // Initialize parameters with pre-detected values
  useEffect(() => {
    const initialParams: Record<string, any> = {};

    // 1. Copy detected entity IDs for both key and key_id
    Object.keys(suggestion.detected_values).forEach((key) => {
      const val = suggestion.detected_values[key];
      initialParams[key] = val.id;
      initialParams[`${key}_id`] = val.id;
    });

    setParamState(initialParams);

    // 2. Fetch dropdown options for missing REFERENCE placeholders
    suggestion.missing_placeholders.forEach((p) => {
      if (p.data_type === 'REFERENCE' && p.source_table) {
        setLoadingOptions((prev) => ({ ...prev, [p.placeholder_name]: true }));
        fetchReferenceOptions(p.source_table)
          .then((res) => {
            setReferenceOptions((prev) => ({ ...prev, [p.placeholder_name]: res.options }));
          })
          .catch((err) => console.error(err))
          .finally(() => {
            setLoadingOptions((prev) => ({ ...prev, [p.placeholder_name]: false }));
          });
      }
    });
  }, [suggestion]);

  const handleSelectChange = (placeholderName: string, selectedId: any) => {
    const parsedVal = parseInt(selectedId) || selectedId;
    setParamState((prev) => ({
      ...prev,
      [placeholderName]: parsedVal,
      [`${placeholderName}_id`]: parsedVal
    }));
  };

  const handleInputChange = (placeholderName: string, val: any) => {
    const parsedVal = typeof val === 'string' ? (parseInt(val) || val) : val;
    setParamState((prev) => ({
      ...prev,
      [placeholderName]: parsedVal,
      [`${placeholderName}_id`]: parsedVal
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onExecute(paramState);
  };

  return (
    <div className="glass-panel" style={{ marginTop: '24px' }}>
      <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
        Template Selection Preview & Parameter Resolution
      </h3>
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
        Intent: <strong style={{ color: 'var(--accent-blue)' }}>{suggestion.intent}</strong> — Selected Pattern: "{suggestion.question_template}"
      </p>

      <form onSubmit={handleSubmit}>
        {/* Pre-filled detected values display */}
        {Object.keys(suggestion.detected_values).length > 0 && (
          <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '10px', padding: '14px', marginBottom: '20px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent-emerald)', textTransform: 'uppercase' }}>
              ✓ Auto-Resolved Parameters
            </span>
            <div style={{ marginTop: '8px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              {Object.keys(suggestion.detected_values).map((key) => {
                const val = suggestion.detected_values[key];
                return (
                  <div key={key} style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                    <strong>{key}:</strong> {val.label} (ID: {val.id})
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Missing Placeholders Input Controls */}
        {suggestion.missing_placeholders.map((p) => (
          <div key={p.placeholder_name} className="form-group" style={{ background: 'var(--bg-card-hover)', padding: '16px', borderRadius: '10px', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0, fontWeight: 600, fontSize: '14px' }}>
                Follow-up: Provide value for <span style={{ color: 'var(--accent-blue)', fontFamily: 'monospace' }}>{p.placeholder_name}</span> {p.required && <span style={{ color: '#ef4444' }}>*</span>}
              </label>

              <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '12px', fontWeight: 700, background: p.data_type === 'REFERENCE' ? 'rgba(37, 99, 235, 0.15)' : 'rgba(245, 158, 11, 0.15)', color: p.data_type === 'REFERENCE' ? 'var(--accent-blue)' : '#f59e0b' }}>
                {p.data_type === 'REFERENCE' ? `📋 Picklist (${p.source_table})` : `⌨️ Continuous Input (${p.data_type})`}
              </span>
            </div>

            {p.data_type === 'REFERENCE' ? (
              <select
                className="form-select"
                required={p.required}
                onChange={(e) => handleSelectChange(p.placeholder_name, e.target.value)}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', background: 'var(--input-bg)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
              >
                <option value="">-- Select {p.placeholder_name} from {p.source_table} picklist --</option>
                {referenceOptions[p.placeholder_name]?.map((opt) => (
                  <option key={opt.id} value={opt.id}>
                    {opt.label} (ID: {opt.id})
                  </option>
                ))}
              </select>
            ) : p.data_type === 'INTEGER' ? (
              <input
                type="number"
                className="form-input"
                placeholder={`Type numeric value for ${p.placeholder_name}...`}
                defaultValue={10}
                required={p.required}
                onChange={(e) => handleInputChange(p.placeholder_name, e.target.value)}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', background: 'var(--input-bg)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
              />
            ) : (
              <input
                type="text"
                className="form-input"
                placeholder={`Type ${p.placeholder_name} value (e.g. CMS20260005678)...`}
                required={p.required}
                onChange={(e) => handleInputChange(p.placeholder_name, e.target.value)}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', background: 'var(--input-bg)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
              />
            )}
          </div>
        ))}

        <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '10px' }} disabled={executing}>
          {executing ? 'Executing Query...' : '⚡ Execute Parameterized SQL Template'}
        </button>
      </form>
    </div>
  );
};
