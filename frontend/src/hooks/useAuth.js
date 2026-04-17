import { useMutation, useQuery } from '@tanstack/react-query';
import client from '../api/client';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ email, password }) => {
      const { data } = await client.post('/auth/login', { email, password });
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token);
      navigate('/dashboard');
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ email, username, password }) => {
      const { data } = await client.post('/auth/register', {
        email,
        username,
        password,
      });
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token);
      navigate('/dashboard');
    },
  });
}

export function useCurrentUser() {
  const token = useAuthStore((s) => s.token);

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await client.get('/auth/me');
      return data;
    },
    enabled: !!token,
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return () => {
    logout();
    navigate('/login');
  };
}
