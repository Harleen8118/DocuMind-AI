import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,

      setAuth: (user, token) =>
        set({ user, token }),

      logout: () =>
        set({ user: null, token: null }),

      updateUser: (user) =>
        set({ user }),
    }),
    {
      name: 'documind-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
);
