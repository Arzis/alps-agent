import { ThemeConfig } from 'antd';

export const lightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 8,
    fontSize: 14,
    colorBgContainer: '#ffffff',
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  components: {
    Layout: {
      siderBg: '#ffffff',
      headerBg: '#ffffff',
      headerHeight: 56,
    },
    Menu: {
      itemBorderRadius: 8,
      itemMarginBlock: 4,
      itemMarginInline: 8,
    },
    Card: {
      borderRadiusLG: 12,
    },
    Button: {
      borderRadius: 8,
    },
  },
};

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 8,
    fontSize: 14,
    colorBgContainer: '#1f1f1f',
    colorBgLayout: '#141414',
    colorText: 'rgba(255, 255, 255, 0.85)',
  },
  components: {
    Layout: {
      siderBg: '#1f1f1f',
      headerBg: '#1f1f1f',
      headerHeight: 56,
    },
  },
};
