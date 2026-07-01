import axios from 'axios';

const rawBackendUrl = (process.env.REACT_APP_BACKEND_URL || '').trim();
export const API = rawBackendUrl ? `${rawBackendUrl.replace(/\/+$/, '')}/api` : '/api';

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('chitra_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('chitra_token');
    }
    return Promise.reject(err);
  }
);

export default api;
