'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';
import { authService } from '../lib/services';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  setUser: (user: User) => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.login({ email, password });
          localStorage.setItem('access_token', response.access_token);
          // Mirror token/role into cookies so Next.js middleware can authorize protected routes
          document.cookie = `auth_token=${response.access_token}; path=/; samesite=strict; secure`;
          document.cookie = `user_role=${response.user.role}; path=/; samesite=strict; secure`;
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
        document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
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

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }
        try {
          const user = await authService.getCurrentUser();
          // Refresh cookies for middleware on page reloads
          document.cookie = `auth_token=${token}; path=/; samesite=strict; secure`;
          document.cookie = `user_role=${user.role}; path=/; samesite=strict; secure`;
          set({ user, isAuthenticated: true, token });
        } catch {
          localStorage.removeItem('access_token');
          document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
          document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
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
    }
  )
);
