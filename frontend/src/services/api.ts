import { SuggestResponse, QueryExecutionResult } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export async function fetchHealthStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('Health fetch error:', err);
    return null;
  }
}

export async function fetchSuggestions(queryText: string): Promise<SuggestResponse> {
  const res = await fetch(`${API_BASE_URL}/query/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: queryText, top_k: 5 })
  });
  if (!res.ok) {
    throw new Error(`Suggestion API error: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchReferenceOptions(sourceTable: string, search: string = '') {
  const url = search
    ? `${API_BASE_URL}/reference/${sourceTable}?q=${encodeURIComponent(search)}`
    : `${API_BASE_URL}/reference/${sourceTable}`;

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Reference API error: ${res.statusText}`);
  }
  return await res.json();
}

export async function executeQueryTemplate(
  templateId: string,
  parameters: Record<string, any>
): Promise<QueryExecutionResult> {
  const res = await fetch(`${API_BASE_URL}/query/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      template_id: templateId,
      parameters: parameters,
      max_rows: 1000
    })
  });
  if (!res.ok) {
    const errBody = await res.json();
    throw new Error(errBody.detail || 'Execution error');
  }
  return await res.json();
}

export async function fetchAdminTemplates(search: string = ''): Promise<any[]> {
  const url = search
    ? `${API_BASE_URL}/admin/templates?q=${encodeURIComponent(search)}`
    : `${API_BASE_URL}/admin/templates`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch templates: ${res.statusText}`);
  }
  return await res.json();
}

export async function createAdminTemplate(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errBody = await res.json();
    throw new Error(errBody.detail || 'Failed to create query template.');
  }
  return await res.json();
}

export async function updateAdminTemplate(templateId: string, payload: any): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/templates/${encodeURIComponent(templateId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errBody = await res.json();
    throw new Error(errBody.detail || 'Failed to update query template.');
  }
  return await res.json();
}

export async function deleteAdminTemplate(templateId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    const errBody = await res.json();
    throw new Error(errBody.detail || 'Failed to delete query template.');
  }
  return await res.json();
}
