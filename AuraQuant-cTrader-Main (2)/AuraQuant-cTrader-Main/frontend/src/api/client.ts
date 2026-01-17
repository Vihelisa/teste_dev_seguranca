import axios from 'axios';

// Create a clean Axios instance WITHOUT the interceptor.
// The AuthContext will be the single source of truth for managing the auth header.
// [PHOENIX COMPLIANCE] Using relative path '/api' to enforce Proxy Pattern.
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;