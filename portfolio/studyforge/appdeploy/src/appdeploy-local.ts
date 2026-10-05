type ApiResponse<T = any> = { data: T };

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

async function request<T = any>(method: Method, url: string, data?: unknown): Promise<ApiResponse<T>> {
  let target = url;
  const init: RequestInit = {
    method,
    credentials: 'include',
    headers: { Accept: 'application/json' },
  };

  if (method === 'GET' && data && typeof data === 'object') {
    const query = new URLSearchParams();
    Object.entries(data as Record<string, unknown>).forEach(([key, value]) => {
      if (value !== undefined && value !== null) query.set(key, String(value));
    });
    const suffix = query.toString();
    if (suffix) target += (target.includes('?') ? '&' : '?') + suffix;
  } else if (data !== undefined) {
    init.headers = { ...init.headers, 'Content-Type': 'application/json' };
    init.body = JSON.stringify(data);
  }

  const response = await fetch(target, init);
  const raw = await response.text();
  let parsed: unknown = {};
  if (raw) {
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = raw;
    }
  }
  if (!response.ok) {
    const message = typeof parsed === 'object' && parsed !== null && 'error' in parsed
      ? String((parsed as { error: unknown }).error)
      : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return { data: parsed as T };
}

export const api = {
  get: <T = any>(url: string, data?: unknown) => request<T>('GET', url, data),
  post: <T = any>(url: string, data?: unknown) => request<T>('POST', url, data),
  put: <T = any>(url: string, data?: unknown) => request<T>('PUT', url, data),
  delete: <T = any>(url: string, data?: unknown) => request<T>('DELETE', url, data),
};
