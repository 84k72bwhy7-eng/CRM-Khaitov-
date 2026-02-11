import { useState, useCallback } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const request = useCallback(async (method, endpoint, data = null, params = null) => {
    setLoading(true);
    setError(null);
    console.log(`[useApi] Starting ${method} ${endpoint}`, { params });
    try {
      const token = localStorage.getItem('crm_token');
      console.log(`[useApi] Token present: ${!!token}`);
      const config = { 
        method, 
        url: `${API_URL}${endpoint}`,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      };
      if (data) config.data = data;
      if (params) config.params = params;
      const response = await axios(config);
      console.log(`[useApi] ${method} ${endpoint} SUCCESS:`, Array.isArray(response.data) ? `${response.data.length} items` : typeof response.data);
      return response.data;
    } catch (err) {
      console.error(`[useApi] ${method} ${endpoint} ERROR:`, err.message, err.response?.status);
      const errorMessage = err.response?.data?.detail || err.message;
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const get = useCallback((endpoint, params) => request('GET', endpoint, null, params), [request]);
  const post = useCallback((endpoint, data) => request('POST', endpoint, data), [request]);
  const put = useCallback((endpoint, data) => request('PUT', endpoint, data), [request]);
  const del = useCallback((endpoint) => request('DELETE', endpoint), [request]);

  return { loading, error, get, post, put, del };
};
