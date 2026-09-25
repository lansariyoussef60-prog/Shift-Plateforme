import axios, { AxiosError, AxiosRequestConfig } from 'axios';

const base = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: base,
  headers: { 'Content-Type': 'application/json' },
});

let access = sessionStorage.getItem('shift_access') || '';

export const setAccess = (token: string) => {
  access = token;
  if (token) sessionStorage.setItem('shift_access', token);
  else sessionStorage.removeItem('shift_access');
};

export const setRefresh = (token: string) => {
  if (token) sessionStorage.setItem('shift_refresh', token);
  else sessionStorage.removeItem('shift_refresh');
};

export const clearAuth = () => {
  access = '';
  sessionStorage.removeItem('shift_access');
  sessionStorage.removeItem('shift_refresh');
};

api.interceptors.request.use((config) => {
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as (AxiosRequestConfig & { __retry?: boolean }) | undefined;

    if (error.response?.status !== 401 || !config || config.__retry) {
      return Promise.reject(error);
    }

    const refreshToken = sessionStorage.getItem('shift_refresh');
    if (!refreshToken) {
      clearAuth();
      return Promise.reject(error);
    }

    try {
      refreshing ??= api
        .post('/auth/refresh', { refresh_token: refreshToken })
        .then((response) => {
          setAccess(response.data.access_token);
          setRefresh(response.data.refresh_token);
          return response.data.access_token as string;
        })
        .finally(() => {
          refreshing = null;
        });

      const token = await refreshing;
      config.__retry = true;
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
      return api(config);
    } catch (refreshError) {
      clearAuth();
      return Promise.reject(refreshError);
    }
  },
);

export const get = <T = any>(url: string, params?: any) =>
  api.get<T>(url, { params }).then((response) => response.data);

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
  api.post<T>(url, data, config).then((response) => response.data);

export const put = <T = any>(url: string, data?: any) =>
  api.put<T>(url, data).then((response) => response.data);

export const patch = <T = any>(url: string, data?: any) =>
  api.patch<T>(url, data).then((response) => response.data);

export const del = <T = any>(url: string) =>
  api.delete<T>(url).then((response) => response.data);

export const errMsg = (error: any) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) return detail.message;
  if (Array.isArray(detail)) return detail.map((item: any) => item?.msg || String(item)).join(', ');
  return error?.message || 'Unexpected error';
};
