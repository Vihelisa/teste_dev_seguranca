import { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { User } from '@/types';
import { fetchUserProfile, loginUser, registerUser } from '@/api';
import apiClient from '@/api/client';

// --- INTERFACES E TIPOS ---
export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterUserInfo {
    email: string;
    password: string;
    name: string;
    phone?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (data: RegisterUserInfo) => Promise<void>;
}

// --- CONTEXTO ---
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// --- HOOK CUSTOMIZADO ---
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider');
  }
  return context;
};

// --- PROVEDOR (PROVIDER) ---
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState<boolean>(false);

  // Efeito que roda apenas na montagem para verificar o token inicial
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        // Configura o header na inicialização para validar o token
        apiClient.defaults.headers.common['Authorization'] = `Token ${storedToken}`;
        try {
          const profile = await fetchUserProfile();
          setUser(profile);
          setToken(storedToken);
        } catch (error) {
          console.error("Auto-login falhou, token inválido.", error);
          // Limpa tudo em caso de falha
          localStorage.removeItem('authToken');
          delete apiClient.defaults.headers.common['Authorization'];
        }
      }
      // Sinaliza que a verificação inicial terminou
      setIsInitialized(true);
    };
    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
  const apiCredentials = { username: credentials.email, password: credentials.password };
  
  // --- ADICIONE ESTE LOG DE DEPURAÇÃO ---
  console.log("Enviando para a API de Login:", apiCredentials);
  // --- FIM DO LOG DE DEPURAÇÃO ---

  const response = await loginUser(apiCredentials);
    const { token: newToken, user: loggedInUser } = response;

    if (!newToken) {
      throw new Error("Login falhou: nenhum token recebido.");
    }

    // [CORREÇÃO CRÍTICA] Atualiza o cabeçalho padrão do apiClient IMEDIATAMENTE
    apiClient.defaults.headers.common['Authorization'] = `Token ${newToken}`;
    
    // Salva o token no localStorage para persistir a sessão
    localStorage.setItem('authToken', newToken);
    
    // Atualiza o estado do React para re-renderizar a aplicação
    setUser(loggedInUser);
    setToken(newToken);
  };

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('authToken');
    delete apiClient.defaults.headers.common['Authorization'];
    // O redirecionamento agora é tratado pelo componente que chama o logout.
  }, []);

  const register = useCallback(async (data: RegisterUserInfo) => {
    // A função de registro pode ser estendida para fazer o login automático
    await registerUser(data);
  }, []);

  // O valor fornecido pelo contexto, memoizado para performance
  const contextValue = useMemo(() => ({
    user,
    token,
    isAuthenticated: !!user,
    isInitialized,
    login,
    logout,
    register,
  }), [user, token, isInitialized, login, logout, register]);

  // Renderiza um placeholder de carregamento até a verificação inicial do token terminar
  if (!isInitialized) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>Inicializando Sessão...</p>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};