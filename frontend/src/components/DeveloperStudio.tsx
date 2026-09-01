import React, { useState, useEffect } from 'react';
import { AdminQueryTemplate, PlaceholderMetadata, QueryExecutionResult } from '../types';
import {
  fetchAdminTemplates,
  createAdminTemplate,
  updateAdminTemplate,
  deleteAdminTemplate,
  executeQueryTemplate,
  fetchUnmatchedQueries
} from '../services/api';
import { ResultTable } from './ResultTable';

export const DeveloperStudio: React.FC = () => {
  const [templates, setTemplates] = useState<AdminQueryTemplate[]>([]);
  const [activeFolder, setActiveFolder] = useState<'verified' | 'unverified' | 'unmatched'>('unverified');
  const [unmatchedQueries, setUnmatchedQueries] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Edit / Create Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<AdminQueryTemplate | null>(null);
  
  // Form State
  const [formData, setFormData] = useState<{
    template_id: string;
    intent: string;
    question_template: string;
    retrieval_text: string;
    sql_template: string;
    result_type: string;
    is_active: boolean;
    is_verified: boolean;
    version: number;
    placeholders: PlaceholderMetadata[];
  }>({
    template_id: '',
    intent: '',
    question_template: '',
    retrieval_text: '',
    sql_template: '',
    result_type: 'tabular',
    is_active: true,
    is_verified: false,
    version: 1,
    placeholders: []
  });

  // Test & Run Sandbox State
  const [testTemplate, setTestTemplate] = useState<AdminQueryTemplate | null>(null);
  const [testParams, setTestParams] = useState<Record<string, any>>({});
  const [testExecuting, setTestExecuting] = useState(false);
  const [testResult, setTestResult] = useState<QueryExecutionResult | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    loadUnmatchedQueries();
  }, []);

  const loadUnmatchedQueries = async () => {
    try {
      const data = await fetchUnmatchedQueries();
      setUnmatchedQueries(data);
    } catch (err) {
      console.error('Failed to load unmatched scope queries', err);
    }
  };

  const handleConvertUnmatchedToTemplate = (unmatchedItem: any) => {
    setEditingTemplate(null);
    const derivedIntent = unmatchedItem.query_text
      ? unmatchedItem.query_text
          .toLowerCase()
          .replace(/[^a-z0-9\s]/g, '')
          .trim()
          .split(/\s+/)
          .slice(0, 4)
          .join('_')
      : 'custom_intent';

    setFormData({
      template_id: `CMP_${Math.floor(100 + Math.random() * 900)}`,
      intent: derivedIntent,
      question_template: unmatchedItem.query_text || '',
      retrieval_text: (unmatchedItem.query_text || '').toLowerCase(),
      sql_template: `SELECT c.complaint_number, c.title, c.created_at, d.department_name, w.ward_name\nFROM complaint c\nJOIN department_master d ON d.id = c.department_id\nJOIN ward_master w ON w.id = c.ward_id\nLIMIT 10;`,
      result_type: 'tabular',
      is_active: true,
      is_verified: false,
      version: 1,
      placeholders: []
    });
    setShowModal(true);
  };

  const loadTemplates = async (search: string = '') => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchAdminTemplates(search);
      setTemplates(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadTemplates(searchTerm);
  };

  const openCreateModal = () => {
    setEditingTemplate(null);
    setFormData({
      template_id: `CMP_${Math.floor(100 + Math.random() * 900)}`,
      intent: '',
      question_template: '',
      retrieval_text: '',
      sql_template: '',
      result_type: 'tabular',
      is_active: true,
      is_verified: activeFolder === 'verified',
      version: 1,
      placeholders: []
    });
    setShowModal(true);
  };

  const openEditModal = (template: AdminQueryTemplate) => {
    setEditingTemplate(template);
    setFormData({
      template_id: template.template_id,
      intent: template.intent,
      question_template: template.question_template,
      retrieval_text: template.retrieval_text,
      sql_template: template.sql_template,
      result_type: template.result_type,
      is_active: template.is_active,
      is_verified: template.is_verified ?? true,
      version: template.version,
      placeholders: template.placeholders || []
    });
    setShowModal(true);
  };

  const handleSaveTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (editingTemplate) {
        await updateAdminTemplate(editingTemplate.template_id, formData);
        setSuccessMsg(`Template '${editingTemplate.template_id}' updated successfully! Vector embedding re-computed.`);
      } else {
        await createAdminTemplate(formData);
        setSuccessMsg(`New Template '${formData.template_id}' created in ${formData.is_verified ? 'Verified' : 'Un-verified'} folder! Vector embedding computed.`);
      }
      setShowModal(false);
      loadTemplates(searchTerm);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save template.');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (!window.confirm(`Are you sure you want to delete template '${templateId}'?`)) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await deleteAdminTemplate(templateId);
      setSuccessMsg(`Template '${templateId}' deleted.`);
      loadTemplates(searchTerm);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to delete template.');
    }
  };

  const handleToggleActive = async (template: AdminQueryTemplate) => {
    try {
      await updateAdminTemplate(template.template_id, { is_active: !template.is_active });
      loadTemplates(searchTerm);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update active status');
    }
  };

  const handleToggleVerified = async (template: AdminQueryTemplate) => {
    try {
      const newStatus = !template.is_verified;
      await updateAdminTemplate(template.template_id, { is_verified: newStatus });
      setSuccessMsg(`Template '${template.template_id}' moved to ${newStatus ? 'Verified' : 'Un-verified'} folder.`);
      loadTemplates(searchTerm);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update verification status');
    }
  };

  // Placeholder form helper
  const addPlaceholder = () => {
    setFormData((prev) => ({
      ...prev,
      placeholders: [
        ...prev.placeholders,
        {
          placeholder_name: `param_${prev.placeholders.length + 1}`,
          data_type: 'REFERENCE',
          input_mode: 'searchable_dropdown',
          source_table: 'department_master',
          source_id_column: 'id',
          source_label_column: 'department_name',
          required: true,
          display_order: prev.placeholders.length + 1
        }
      ]
    }));
  };

  const removePlaceholder = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      placeholders: prev.placeholders.filter((_, i) => i !== index)
    }));
  };

  const updatePlaceholder = (index: number, key: keyof PlaceholderMetadata, val: any) => {
    setFormData((prev) => {
      const updated = [...prev.placeholders];
      updated[index] = { ...updated[index], [key]: val };
      return { ...prev, placeholders: updated };
    });
  };

  // Open Test & Run Sandbox
  const openTestSandbox = (template: AdminQueryTemplate) => {
    setTestTemplate(template);
    setTestResult(null);
    setTestError(null);
    // Initialize default parameter values
    const initial: Record<string, any> = {};
    template.placeholders.forEach((p) => {
      if (p.data_type === 'INTEGER') initial[p.placeholder_name] = 5;
      else if (p.data_type === 'REFERENCE') initial[`${p.placeholder_name}_id`] = 1;
      else initial[p.placeholder_name] = '';
    });
    setTestParams(initial);
  };

  const handleRunTestQuery = async () => {
    if (!testTemplate) return;
    setTestExecuting(true);
    setTestError(null);
    setTestResult(null);

    try {
      const result = await executeQueryTemplate(testTemplate.template_id, testParams);
      setTestResult(result);
    } catch (err: any) {
      setTestError(err.message || 'Error executing query template');
    } finally {
      setTestExecuting(false);
    }
  };

  return (
    <div style={{ marginTop: '24px' }}>
      {/* Header Bar */}
      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            🛠️ Query Template Developer Studio
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
            Manage canonical templates, configure typed placeholders, inspect embeddings in PostgreSQL metadata DB, and test query execution.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          style={{
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: '#ffffff',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '10px',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
            transition: 'transform 0.15s ease'
          }}
        >
          ➕ Create New Template
        </button>
      </div>

      {/* Folder Tabs: Verified vs Un-verified */}
      <div style={{ display: 'flex', gap: '12px', marginTop: '16px', marginBottom: '8px' }}>
        <button
          type="button"
          onClick={() => setActiveFolder('verified')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            border: '1px solid',
            borderColor: activeFolder === 'verified' ? 'var(--accent-blue)' : 'var(--border-color)',
            background: activeFolder === 'verified' ? 'rgba(37, 99, 235, 0.15)' : 'var(--bg-card)',
            color: activeFolder === 'verified' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            transition: 'all 0.2s ease'
          }}
        >
          📁 Verified Templates
          <span style={{
            background: activeFolder === 'verified' ? 'var(--accent-blue)' : 'var(--bg-card-hover)',
            color: activeFolder === 'verified' ? '#fff' : 'var(--text-muted)',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 700
          }}>
            {templates.filter(t => t.is_verified !== false).length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveFolder('unverified')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            border: '1px solid',
            borderColor: activeFolder === 'unverified' ? '#f59e0b' : 'var(--border-color)',
            background: activeFolder === 'unverified' ? 'rgba(245, 158, 11, 0.15)' : 'var(--bg-card)',
            color: activeFolder === 'unverified' ? '#f59e0b' : 'var(--text-secondary)',
            transition: 'all 0.2s ease'
          }}
        >
          📂 Un-verified Templates
          <span style={{
            background: activeFolder === 'unverified' ? '#f59e0b' : 'var(--bg-card-hover)',
            color: activeFolder === 'unverified' ? '#fff' : 'var(--text-muted)',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 700
          }}>
            {templates.filter(t => t.is_verified === false).length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveFolder('unmatched')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            border: '1px solid',
            borderColor: activeFolder === 'unmatched' ? '#ec4899' : 'var(--border-color)',
            background: activeFolder === 'unmatched' ? 'rgba(236, 72, 153, 0.15)' : 'var(--bg-card)',
            color: activeFolder === 'unmatched' ? '#ec4899' : 'var(--text-secondary)',
            transition: 'all 0.2s ease'
          }}
        >
          📥 Scope Backlog (Unmatched)
          <span style={{
            background: activeFolder === 'unmatched' ? '#ec4899' : 'var(--bg-card-hover)',
            color: activeFolder === 'unmatched' ? '#fff' : 'var(--text-muted)',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 700
          }}>
            {unmatchedQueries.length}
          </span>
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="glass-panel" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', marginTop: '16px' }}>
          ⚠️ {errorMsg}
        </div>
      )}
      {successMsg && (
        <div className="glass-panel" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', background: 'rgba(16, 185, 129, 0.1)', color: '#34d399', marginTop: '16px' }}>
          ✅ {successMsg}
        </div>
      )}

      {/* Search & Filter */}
      {activeFolder !== 'unmatched' && (
        <form onSubmit={handleSearchSubmit} style={{ margin: '20px 0', display: 'flex', gap: '12px' }}>
          <input
            type="text"
            placeholder="Search by Template ID, Intent, or Question..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              flex: 1,
              background: 'var(--input-bg)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '10px 16px',
              borderRadius: '10px',
              outline: 'none',
              fontSize: '14px'
            }}
          />
          <button
            type="submit"
            style={{
              background: 'var(--accent-blue)',
              color: '#fff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Search
          </button>
        </form>
      )}

      {/* Main Folder Views */}
      {activeFolder === 'unmatched' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '16px' }}>
          {unmatchedQueries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }} className="glass-panel">
              🎉 No unmatched scope queries logged! All asked queries currently match canonical templates.
            </div>
          ) : (
            unmatchedQueries.map((item, idx) => (
              <div key={item.id || idx} className="glass-panel" style={{ borderLeft: '4px solid #ec4899', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ flex: 1, minWidth: '280px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', background: 'rgba(236, 72, 153, 0.15)', color: '#ec4899', fontWeight: 700, padding: '2px 8px', borderRadius: '6px' }}>
                        Log #{item.id}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        📅 {item.logged_at ? new Date(item.logged_at).toLocaleString() : 'Just now'}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 8px' }}>
                      🗣️ "{item.query_text}"
                    </h3>

                    <div style={{ fontSize: '12.5px', background: 'var(--bg-card-hover)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px 12px', margin: '8px 0', color: 'var(--text-secondary)' }}>
                      <strong>LLM Scope Reason:</strong> {item.reason}
                    </div>

                    {item.candidate_template_ids && item.candidate_template_ids.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '6px' }}>
                        <span>Candidates Evaluated:</span>
                        {item.candidate_template_ids.map((cid: string) => (
                          <span key={cid} style={{ background: 'var(--input-bg)', border: '1px solid var(--border-color)', padding: '1px 6px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '11px' }}>
                            {cid}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleConvertUnmatchedToTemplate(item)}
                    style={{
                      background: 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)',
                      color: '#fff',
                      border: 'none',
                      padding: '8px 14px',
                      borderRadius: '8px',
                      fontWeight: 600,
                      fontSize: '12.5px',
                      cursor: 'pointer',
                      boxShadow: '0 3px 10px rgba(236, 72, 153, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    ➕ Convert to Template
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading templates from PostgreSQL metadata DB...
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
          {templates
            .filter(t => activeFolder === 'verified' ? t.is_verified !== false : t.is_verified === false)
            .map((tpl, index) => (
            <div key={tpl.template_id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: 700, background: 'rgba(37, 99, 235, 0.15)', color: 'var(--accent-blue)', padding: '2px 8px', borderRadius: '6px', fontSize: '13px' }}>
                    #{index + 1}. {tpl.template_id}
                  </span>

                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: tpl.is_verified !== false ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: tpl.is_verified !== false ? 'var(--accent-emerald)' : '#f59e0b', fontWeight: 600 }}>
                      {tpl.is_verified !== false ? 'VERIFIED' : 'UN-VERIFIED'}
                    </span>
                    <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: tpl.is_active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: tpl.is_active ? 'var(--accent-emerald)' : '#ef4444', fontWeight: 600 }}>
                      {tpl.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                </div>

                <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0' }}>
                  {tpl.question_template}
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 10px 0', fontFamily: 'monospace' }}>
                  Intent: {tpl.intent}
                </p>

                {/* Placeholders tags */}
                {tpl.placeholders.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '12px' }}>
                    {tpl.placeholders.map((p) => (
                      <span key={p.placeholder_name} style={{ fontSize: '11px', background: 'var(--bg-card-hover)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '2px 6px', borderRadius: '4px' }}>
                        {p.placeholder_name} ({p.data_type})
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Card Actions */}
              <div style={{ display: 'flex', gap: '6px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', flexWrap: 'wrap' }}>
                <button
                  onClick={() => openTestSandbox(tpl)}
                  style={{
                    flex: 1,
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: 'var(--accent-emerald)',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  ⚡ Test & Run
                </button>
                <button
                  onClick={() => openEditModal(tpl)}
                  style={{
                    background: 'rgba(59, 130, 246, 0.15)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: 'var(--accent-blue)',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => handleToggleVerified(tpl)}
                  title={tpl.is_verified !== false ? 'Move to Un-verified folder' : 'Move to Verified folder'}
                  style={{
                    background: tpl.is_verified !== false ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid ' + (tpl.is_verified !== false ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'),
                    color: tpl.is_verified !== false ? '#f59e0b' : 'var(--accent-emerald)',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {tpl.is_verified !== false ? 'Un-verify' : 'Verify ✓'}
                </button>
                <button
                  onClick={() => handleDeleteTemplate(tpl.template_id)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE / EDIT MODAL */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)', zIndex: 100, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '720px', maxHeight: '90vh', overflowY: 'auto', background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                {editingTemplate ? `Edit Template '${editingTemplate.template_id}'` : 'Create New Query Template'}
              </h3>
              <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '20px', cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveTemplate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Template ID</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingTemplate}
                    placeholder="e.g. CMP_819"
                    value={formData.template_id}
                    onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Intent Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. pending_complaints_by_department"
                    value={formData.intent}
                    onChange={(e) => setFormData({ ...formData, intent: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Natural Language Question Template (Display)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. How many pending complaints in {department}?"
                  value={formData.question_template}
                  onChange={(e) => setFormData({ ...formData, question_template: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Retrieval Text (Used for Vector Embedding matching)</label>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. count open pending complaints filtered by department"
                  value={formData.retrieval_text}
                  onChange={(e) => setFormData({ ...formData, retrieval_text: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px', fontFamily: 'monospace' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Parameterized SQL Query Template</label>
                <textarea
                  required
                  rows={4}
                  placeholder="SELECT COUNT(*) FROM complaint WHERE department_id = :department_id AND closed_at IS NULL;"
                  value={formData.sql_template}
                  onChange={(e) => setFormData({ ...formData, sql_template: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--accent-blue)', borderRadius: '6px', fontFamily: 'monospace', fontSize: '12px' }}
                />
              </div>

              {/* Target Folder Selection */}
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Verification Folder Destination</label>
                <select
                  value={formData.is_verified ? 'verified' : 'unverified'}
                  onChange={(e) => setFormData({ ...formData, is_verified: e.target.value === 'verified' })}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px', fontSize: '13px' }}
                >
                  <option value="verified">📁 Verified Queries Folder</option>
                  <option value="unverified">📂 Un-verified Queries Folder</option>
                </select>
              </div>

              {/* Placeholders Editor */}
              <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Typed Placeholders ({formData.placeholders.length})</label>
                  <button type="button" onClick={addPlaceholder} style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.4)', color: 'var(--accent-blue)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 600 }}>
                    + Add Placeholder
                  </button>
                </div>

                {formData.placeholders.map((p, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-card-hover)', padding: '10px', borderRadius: '8px', marginBottom: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 30px', gap: '8px', alignItems: 'center' }}>
                      <input
                        type="text"
                        placeholder="Name (e.g. department)"
                        value={p.placeholder_name}
                        onChange={(e) => updatePlaceholder(idx, 'placeholder_name', e.target.value)}
                        style={{ padding: '6px 8px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px', fontSize: '12px' }}
                      />
                      <select
                        value={p.data_type}
                        onChange={(e) => updatePlaceholder(idx, 'data_type', e.target.value)}
                        style={{ padding: '6px 8px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px', fontSize: '12px' }}
                      >
                        <option value="REFERENCE">REFERENCE (DB Lookup)</option>
                        <option value="INTEGER">INTEGER</option>
                        <option value="ENUM">ENUM</option>
                        <option value="DATE_RANGE">DATE_RANGE</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Source Table (e.g. department_master)"
                        value={p.source_table || ''}
                        onChange={(e) => updatePlaceholder(idx, 'source_table', e.target.value)}
                        style={{ padding: '6px 8px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px', fontSize: '12px' }}
                      />
                      <button type="button" onClick={() => removePlaceholder(idx)} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px' }}>
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Submit / Cancel Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                <button type="button" onClick={() => setShowModal(false)} style={{ padding: '8px 16px', background: 'var(--bg-card-hover)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', borderRadius: '8px', cursor: 'pointer' }}>
                  Cancel
                </button>
                <button type="submit" style={{ padding: '8px 20px', background: 'linear-gradient(135deg, #3b82f6, #2563eb)', border: 'none', color: '#fff', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}>
                  {editingTemplate ? 'Save Changes' : 'Create Template'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TEST & RUN SANDBOX DRAWER */}
      {testTemplate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(6px)', zIndex: 110, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto', background: 'var(--bg-card)', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--accent-emerald)', margin: 0 }}>
                  ⚡ Test & Run Query Sandbox: {testTemplate.template_id}
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                  Execute SQL template directly against PMC database and inspect output dataset.
                </p>
              </div>
              <button onClick={() => setTestTemplate(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '22px', cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            {/* Template SQL snippet */}
            <div style={{ background: 'var(--input-bg)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '16px', fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent-blue)' }}>
              {testTemplate.sql_template}
            </div>

            {/* Test Parameter Inputs */}
            {testTemplate.placeholders.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '8px' }}>Test Parameter Inputs</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
                  {testTemplate.placeholders.map((p) => {
                    const key = p.data_type === 'REFERENCE' ? `${p.placeholder_name}_id` : p.placeholder_name;
                    return (
                      <div key={p.placeholder_name}>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                          {p.placeholder_name} ({p.data_type})
                        </label>
                        <input
                          type={p.data_type === 'INTEGER' ? 'number' : 'text'}
                          placeholder={`Enter ${key}`}
                          value={testParams[key] ?? ''}
                          onChange={(e) => setTestParams({ ...testParams, [key]: p.data_type === 'INTEGER' ? Number(e.target.value) : e.target.value })}
                          style={{ width: '100%', padding: '8px 10px', background: 'var(--input-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '6px', fontSize: '13px' }}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <button
              onClick={handleRunTestQuery}
              disabled={testExecuting}
              style={{
                width: '100%',
                padding: '12px',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                marginBottom: '16px'
              }}
            >
              {testExecuting ? 'Executing Query against PMC DB...' : '▶ Run Query'}
            </button>

            {testError && (
              <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', fontSize: '13px', marginBottom: '16px' }}>
                ⚠️ {testError}
              </div>
            )}

            {testResult && (
              <div>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '12px', fontSize: '13px', color: '#34d399', fontWeight: 600 }}>
                  <span>Status: {testResult.status}</span>
                  <span>Execution Time: {testResult.execution_time_ms} ms</span>
                  <span>Total Rows: {testResult.total_rows}</span>
                </div>
                <ResultTable result={testResult} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
