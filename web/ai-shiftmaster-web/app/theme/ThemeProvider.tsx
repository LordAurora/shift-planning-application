'use client';

import React from 'react';
import { ConfigProvider, App } from 'antd';
import theme from './themeConfig';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  return (
    <ConfigProvider theme={theme}>
      <App>{children}</App>
    </ConfigProvider>
  );
}
