'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Spin } from 'antd';
import { useAuthStore } from './store/authStore';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    } else {
      // Giriş yapmamış kullanıcıları landing page'e yönlendir
      router.push('/landing');
    }
  }, [isAuthenticated, router]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f5f5f5'
    }}>
      <Spin size="large" />
    </div>
  );
}
