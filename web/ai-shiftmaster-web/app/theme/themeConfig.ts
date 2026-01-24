import type { ThemeConfig } from 'antd';

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1e3a5f',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorText: '#1f1f1f',
    colorTextSecondary: '#595959',
    borderRadius: 4,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#1e3a5f',
      bodyBg: '#f5f5f5',
    },
    Menu: {
      darkItemBg: '#1e3a5f',
      darkItemColor: '#ffffff',
      darkItemHoverBg: '#2d4a6f',
      darkItemSelectedBg: '#0d2a4f',
    },
    Button: {
      primaryColor: '#ffffff',
    },
    Table: {
      headerBg: '#fafafa',
      headerColor: '#1f1f1f',
    },
  },
};

export default theme;
