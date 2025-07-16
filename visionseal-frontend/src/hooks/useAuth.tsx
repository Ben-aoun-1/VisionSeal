import { useState, useEffect, useContext, createContext, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  email_verified: boolean;
  created_at: string;
  last_sign_in?: string;
  user_metadata?: any;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (userData: RegisterData) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
  sector?: string;
  address?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const isAuthenticated = !!user;

  // Get stored tokens
  const getStoredTokens = () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    return { accessToken, refreshToken };
  };

  // Store tokens
  const storeTokens = (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  };

  // Clear tokens
  const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  // API call helper
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const { accessToken } = getStoredTokens();
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options.headers,
      },
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token might be expired, try to refresh
        const refreshed = await refreshToken();
        if (refreshed) {
          // Retry the request with new token
          const { accessToken: newAccessToken } = getStoredTokens();
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${newAccessToken}`,
          };
          return fetch(`${API_BASE_URL}${endpoint}`, config);
        } else {
          // Refresh failed, logout
          await logout();
          throw new Error('Session expired. Please login again.');
        }
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  };

  // Login function
  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        storeTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Login failed' };
      }
    } catch (error: any) {
      return { success: false, error: error.message || 'Network error' };
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (userData: RegisterData): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userData.email,
          password: userData.password,
          first_name: userData.firstName,
          last_name: userData.lastName,
          company: userData.company,
          phone: userData.phone,
          sector: userData.sector,
          address: userData.address,
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        return { success: true };
      } else {
        // Handle validation errors from backend
        let errorMessage = 'Registration failed';
        if (data.detail && Array.isArray(data.detail) && data.detail.length > 0) {
          errorMessage = data.detail[0].msg || data.detail[0].message || errorMessage;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        }
        return { success: false, error: errorMessage };
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      return { success: false, error: error.message || 'Network error' };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      const { accessToken } = getStoredTokens();
      
      if (accessToken) {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearTokens();
      setUser(null);
      navigate('/login');
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    try {
      const { refreshToken: storedRefreshToken } = getStoredTokens();
      
      if (!storedRefreshToken) {
        return false;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: storedRefreshToken }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        storeTokens(data.access_token, data.refresh_token);
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  };

  // Get current user
  const getCurrentUser = async () => {
    try {
      const response = await apiCall('/api/v1/auth/me');
      const data = await response.json();
      
      if (data.success) {
        setUser(data.data);
      }
    } catch (error) {
      console.error('Get current user error:', error);
      clearTokens();
      setUser(null);
    }
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const { accessToken } = getStoredTokens();
      
      if (accessToken) {
        try {
          await getCurrentUser();
        } catch (error) {
          console.error('Auth check error:', error);
          clearTokens();
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};