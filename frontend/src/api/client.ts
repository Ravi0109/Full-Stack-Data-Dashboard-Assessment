import type {
  CurrencyContext,
  Filters,
  Metadata,
  OrdersResponse,
  SortState,
  SummaryResponse,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

class ApiRequestError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.details = details;
  }
}

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, params?: Record<string, QueryValue>) {
  const url = new URL(path, API_URL);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    if (value === 'all') return;
    url.searchParams.set(key, String(value));
  });
  return url.toString();
}

async function request<T>(path: string, options?: RequestInit, params?: Record<string, QueryValue>) {
  const response = await fetch(buildUrl(path, params), {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiRequestError(payload.error ?? 'Request failed', response.status, payload.details);
  }
  return payload as T;
}

function filterParams(filters: Filters): Record<string, QueryValue> {
  return {
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
    category: filters.category,
    status: filters.status,
    delayed: filters.delayed,
    search: filters.search,
  };
}

export const api = {
  getOrders(
    filters: Filters,
    sort: SortState,
    page: number,
    pageSize: number,
    signal?: AbortSignal,
  ) {
    return request<OrdersResponse>(
      '/orders',
      { signal },
      {
        ...filterParams(filters),
        sort_by: sort.sortBy,
        sort_dir: sort.sortDir,
        page,
        page_size: pageSize,
      },
    );
  },

  getSummary(filters: Filters, signal?: AbortSignal) {
    return request<SummaryResponse>('/analytics/summary', { signal }, filterParams(filters));
  },

  getMetadata(signal?: AbortSignal) {
    return request<Metadata>('/metadata', { signal });
  },

  getCurrencyContext(signal?: AbortSignal) {
    return request<CurrencyContext>('/external/currency-context', { signal });
  },

  ingestAll() {
    return request<Metadata & { message: string }>('/ingest/all', { method: 'POST' });
  },
};

export { ApiRequestError };
