'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

/**
 * User interface
 */
export interface User {
  id: number;
  email: string;
  name: string;
  role: 'super_admin' | 'admin' | 'manager' | 'supervisor' | 'employee';
  department_id?: number;
  department_name?: string;
  avatar_url?: string;
}

/**
 * Permission type
 */
export type Permission = 
  | 'shift:view:own'
  | 'shift:view:team'
  | 'shift:view:all'
  | 'shift:create'
  | 'shift:update'
  | 'shift:delete'
  | 'employee:view:own'
  | 'employee:view:team'
  | 'employee:view:all'
  | 'employee:create'
  | 'employee:update'
  | 'leave:view:own'
  | 'leave:view:team'
  | 'leave:view:all'
  | 'leave:approve'
  | 'rule:view'
  | 'rule:create'
  | 'rule:update'
  | 'ai:optimize'
  | 'analytics:view'
  | 'audit:view'
  | 'settings:manage';

/**
 * Role permissions map
 */
const ROLE_PERMISSIONS: Record<User['role'], Permission[]> = {
  super_admin: [
    'shift:view:all', 'shift:create', 'shift:update', 'shift:delete',
    'employee:view:all', 'employee:create', 'employee:update',
    'leave:view:all', 'leave:approve',
    'rule:view', 'rule:create', 'rule:update',
    'ai:optimize', 'analytics:view', 'audit:view', 'settings:manage',
  ],
  admin: [
    'shift:view:all', 'shift:create', 'shift:update', 'shift:delete',
    'employee:view:all', 'employee:create', 'employee:update',
    'leave:view:all', 'leave:approve',
    'rule:view', 'rule:create', 'rule:update',
    'ai:optimize', 'analytics:view', 'audit:view',
  ],
  manager: [
    'shift:view:team', 'shift:create', 'shift:update',
    'employee:view:team', 'employee:create',
    'leave:view:team', 'leave:approve',
    'rule:view',
    'ai:optimize', 'analytics:view',
  ],
  supervisor: [
    'shift:view:team',
    'employee:view:team',
    'leave:view:team',
    'rule:view',
  ],
  employee: [
    'shift:view:own',
    'employee:view:own',
    'leave:view:own',
  ],
};

/**
 * Auth context interface
 */
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  canAccessRoute: (route: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Auth Provider component
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Token refresh interval
  useEffect(() => {
    if (!user) return;

    // Refresh token every 14 minutes (token expires in 15 min)
    const interval = setInterval(() => {
      refreshToken();
    }, 14 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user]);

  /**
   * Check if user is authenticated
   */
  async function checkAuth() {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      const response = await fetch('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        
        // Set cookie for middleware
        document.cookie = `auth_token=${token}; path=/; secure; samesite=strict`;
        document.cookie = `user_role=${userData.role}; path=/; secure; samesite=strict`;
      } else {
        // Token invalid, clear storage
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setIsLoading(false);
    }
  }

  /**
   * Login user
   */
  async function login(email: string, password: string) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    
    // Store tokens
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Set cookies for middleware
    document.cookie = `auth_token=${data.access_token}; path=/; secure; samesite=strict`;
    document.cookie = `user_role=${data.user.role}; path=/; secure; samesite=strict`;
    
    setUser(data.user);
    router.push('/dashboard');
  }

  /**
   * Logout user
   */
  async function logout() {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear storage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      
      setUser(null);
      router.push('/login');
    }
  }

  /**
   * Refresh access token
   */
  async function refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return;

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        document.cookie = `auth_token=${data.access_token}; path=/; secure; samesite=strict`;
        
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
      } else {
        // Refresh failed, logout
        await logout();
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
  }

  /**
   * Check if user has a specific permission
   */
  function hasPermission(permission: Permission): boolean {
    if (!user) return false;
    const permissions = ROLE_PERMISSIONS[user.role] || [];
    return permissions.includes(permission);
  }

  /**
   * Check if user has any of the specified permissions
   */
  function hasAnyPermission(permissions: Permission[]): boolean {
    return permissions.some(p => hasPermission(p));
  }

  /**
   * Check if user has all specified permissions
   */
  function hasAllPermissions(permissions: Permission[]): boolean {
    return permissions.every(p => hasPermission(p));
  }

  /**
   * Check if user can access a specific route
   */
  function canAccessRoute(route: string): boolean {
    if (!user) return false;

    const routePermissions: Record<string, Permission[]> = {
      '/employees': ['employee:view:all', 'employee:view:team'],
      '/shifts': ['shift:view:all', 'shift:view:team', 'shift:view:own'],
      '/rules': ['rule:view'],
      '/ai-optimization': ['ai:optimize'],
      '/settings': ['settings:manage'],
    };

    const requiredPermissions = Object.entries(routePermissions).find(
      ([path]) => route.startsWith(path)
    );

    if (!requiredPermissions) return true; // No specific permissions required
    
    return hasAnyPermission(requiredPermissions[1]);
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canAccessRoute,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * HOC for protected routes (client-side)
 */
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requiredPermissions?: Permission[]
) {
  return function ProtectedRoute(props: P) {
    const { user, isLoading, isAuthenticated, hasAllPermissions } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        router.push('/login');
      }

      if (!isLoading && isAuthenticated && requiredPermissions) {
        if (!hasAllPermissions(requiredPermissions)) {
          router.push('/dashboard');
        }
      }
    }, [isLoading, isAuthenticated, router]);

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    if (requiredPermissions && !hasAllPermissions(requiredPermissions)) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}
