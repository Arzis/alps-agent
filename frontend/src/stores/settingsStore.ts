import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // 主题设置
  theme: 'light' | 'dark';
  primaryColor: string;

  // 知识库设置
  defaultCollection: string;

  // UI 设置
  showCitationPanel: boolean;
  compactMode: boolean;

  // Actions
  setTheme: (theme: 'light' | 'dark') => void;
  setPrimaryColor: (color: string) => void;
  setDefaultCollection: (collection: string) => void;
  setShowCitationPanel: (show: boolean) => void;
  setCompactMode: (compact: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light',
      primaryColor: '#1677ff',
      defaultCollection: 'default',
      showCitationPanel: true,
      compactMode: false,

      setTheme: (theme) => set({ theme }),
      setPrimaryColor: (color) => set({ primaryColor: color }),
      setDefaultCollection: (collection) =>
        set({ defaultCollection: collection }),
      setShowCitationPanel: (show) => set({ showCitationPanel: show }),
      setCompactMode: (compact) => set({ compactMode: compact }),
    }),
    {
      name: 'settings-storage',
    }
  )
);
