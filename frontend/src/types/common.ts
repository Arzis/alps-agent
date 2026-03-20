// 通用类型定义

export interface BaseResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
  request_id?: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorResponse {
  success: false;
  error: ErrorDetail;
  request_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthStatus {
  status: 'ok' | 'healthy' | 'degraded';
  version: string;
}

export interface HealthCheckDetail extends HealthStatus {
  checks: {
    postgres?: { status: string; latency_ms?: number; error?: string | null };
    redis?: { status: string; latency_ms?: number; error?: string | null };
    milvus?: { status: string; latency_ms?: number; error?: string | null };
  };
}
