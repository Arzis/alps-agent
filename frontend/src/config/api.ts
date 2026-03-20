// API 基础配置
const API_BASE = import.meta.env.VITE_API_BASE || '';

export const API_ENDPOINTS = {
  // Health
  health: `${API_BASE}/health`,
  healthDetail: `${API_BASE}/health/detail`,

  // Chat
  chatCompletions: `${API_BASE}/api/v1/chat/completions`,
  chatStream: `${API_BASE}/api/v1/chat/completions/stream`,
  chatSessions: `${API_BASE}/api/v1/chat/sessions`,
  chatHistory: (sessionId: string) =>
    `${API_BASE}/api/v1/chat/sessions/${sessionId}/history`,
  chatDeleteSession: (sessionId: string) =>
    `${API_BASE}/api/v1/chat/sessions/${sessionId}`,

  // Documents
  documentsUpload: `${API_BASE}/api/v1/documents/upload`,
  documents: `${API_BASE}/api/v1/documents/`,
  documentInfo: (docId: string) =>
    `${API_BASE}/api/v1/documents/${docId}`,

  // Evaluation
  evaluationRun: `${API_BASE}/api/v1/evaluation/run`,
  evaluationGenerate: `${API_BASE}/api/v1/evaluation/generate-testset`,
  evaluationReports: `${API_BASE}/api/v1/evaluation/reports`,
  evaluationReportDetail: (runId: string) =>
    `${API_BASE}/api/v1/evaluation/reports/${runId}`,
};

export default API_ENDPOINTS;
