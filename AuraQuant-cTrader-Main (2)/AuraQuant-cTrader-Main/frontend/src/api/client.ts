import axios from 'axios';

// [PHOENIX COMPLIANCE] Using relative path '/api' to enforce Proxy Pattern.
const apiClient = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// INTERCEPTOR DE REQUEST — Injeta token em toda requisição
// ============================================================================
// Centraliza aqui em vez de depender do AuthContext para cada chamada.
// Lê o token do localStorage no momento de cada request (sempre atualizado).
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================================================
// INTERCEPTOR DE RESPONSE — Logout automático em 401
// ============================================================================
// Se o token expirou ou é inválido, o backend retorna 401.
// Sem este interceptor, o usuário continua clicando em botões que não funcionam
// sem receber nenhum feedback — o "Token Silencioso" do audit.
apiClient.interceptors.response.use(
  (response) => response, // Sucesso: passa direto
  (error) => {
    if (error.response?.status === 401) {
      // Remove token inválido
      localStorage.removeItem('authToken');
      // Redireciona para login sem depender do React Router
      // (funciona mesmo se o contexto estiver quebrado)
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;