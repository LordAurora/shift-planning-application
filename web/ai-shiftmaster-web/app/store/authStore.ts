'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';
import { authService } from '../lib/services';

const getCookieSecuritySuffix = () => {
  if (typeof window === 'undefined') {
    return '';
  }
  return window.location.protocol === 'https:' ? '; secure' : '';
};

const setAuthCookies = (token: string, role: string) => {
  const securitySuffix = getCookieSecuritySuffix();
  document.cookie = `auth_token=${token}; path=/; samesite=strict${securitySuffix}`;
  document.cookie = `user_role=${role}; path=/; samesite=strict${securitySuffix}`;
};

const clearAuthCookies = () => {
  document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
};

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  setUser: (user: User) => void;
  setHasHydrated: (value: boolean) => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      hasHydrated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.login({ email, password });
          localStorage.setItem('access_token', response.access_token);
          // Mirror token/role into cookies so Next.js middleware can authorize protected routes
          setAuthCookies(response.access_token, response.user.role);
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
          return true;
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed. Please check your credentials.';
          set({
            error: errorMessage,
            isLoading: false,
          });
          return false;
        }
      },

      logout: () => {
        localStorage.removeItem('access_token');
        clearAuthCookies();
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      setUser: (user: User) => {
        set({ user });
      },

      setHasHydrated: (value: boolean) => {
        set({ hasHydrated: value });
      },

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          clearAuthCookies();
          set({ isAuthenticated: false, user: null });
          return;
        }
        try {
          const user = await authService.getCurrentUser();
          // Refresh cookies for middleware on page reloads
          setAuthCookies(token, user.role);
          set({ user, isAuthenticated: true, token });
        } catch {
          localStorage.removeItem('access_token');
          clearAuthCookies();
          set({ isAuthenticated: false, user: null, token: null });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
