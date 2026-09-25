// Backend URL comes from frontend/.env (VITE_API_URL)
export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error(`Can't reach the server at ${API_URL}. Is the backend running?`);
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data;
}

export function getDocuments() {
  return request('/api/documents');
}

export function uploadDocument(file) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/documents', { method: 'POST', body: form });
}

export function deleteDocument(id) {
  return request(`/api/documents/${id}`, { method: 'DELETE' });
}

export function downloadUrl(id) {
  return `${API_URL}/api/documents/${id}/download`;
}

export function askQuestion(question) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}
