import { useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';

export function useAuth() {
  const { user, token, isAuthenticated, login, logout, updateUser } =
    useAuthStore();

  const isAdmin = user?.role === 'admin';
  const isReviewer = user?.role === 'reviewer' || user?.role === 'admin';

  const hasPermission = useCallback(
    (requiredRole: 'admin' | 'reviewer' | 'user') => {
      if (!isAuthenticated) return false;

      switch (requiredRole) {
        case 'admin':
          return isAdmin;
        case 'reviewer':
          return isReviewer;
        case 'user':
          return true;
        default:
          return false;
      }
    },
    [isAuthenticated, isAdmin, isReviewer]
  );

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    isReviewer,
    login,
    logout,
    updateUser,
    hasPermission,
  };
}
