import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  user_id: string
  username: string
  created_at?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean

  // Actions
  login: (user: User, token: string) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (user, token) =>
        set({
          user,
          token,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),

      updateUser: (updates) =>
        set((s) => ({
          user: s.user ? { ...s.user, ...updates } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
)
