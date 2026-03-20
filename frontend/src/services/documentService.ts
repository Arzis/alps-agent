import request from './request';
import API_ENDPOINTS from '@/config/api';
import type {
  DocumentInfo,
  DocumentUploadResponse,
  DocumentListResponse,
} from '@/types/document';

// 上传文档
export async function uploadDocument(
  file: File,
  collection = 'default',
  onProgress?: (percent: number) => void
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('collection', collection);

  const res = await request.post(API_ENDPOINTS.documentsUpload, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percent);
      }
    },
  });

  return res.data;
}

// 获取文档列表
export async function getDocuments(
  collection = 'default',
  page = 1,
  pageSize = 20
): Promise<DocumentListResponse> {
  const res = await request.get(API_ENDPOINTS.documents, {
    params: { collection, page, page_size: pageSize },
  });
  return res.data;
}

// 获取文档详情
export async function getDocumentInfo(docId: string): Promise<DocumentInfo> {
  const res = await request.get(API_ENDPOINTS.documentInfo(docId));
  return res.data;
}

// 删除文档
export async function deleteDocument(docId: string): Promise<void> {
  await request.delete(API_ENDPOINTS.documentInfo(docId));
}
