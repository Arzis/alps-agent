// 文档相关类型定义

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  collection: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  doc_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
  page: number;
  page_size: number;
}
