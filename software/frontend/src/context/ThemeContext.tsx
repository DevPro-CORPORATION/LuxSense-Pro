import React, { createContext, useContext, useEffect, useState } from 'react';
import { bridge } from '../bridge/bridgeClient';
import { UserSettings } from '../types';

export type ThemeMode = 'dark' | 'light';
export type ResolvedTheme = 'dark' | 'light';

interface ThemeContextType {
  theme: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  resolvedTheme: 'dark',
  setTheme: () => {},
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeMode>('dark');

  // Load initial saved theme from settings
  useEffect(() => {
    bridge.getSettings().then((s: UserSettings | null) => {
      if (s?.theme && (s.theme === 'dark' || s.theme === 'light')) {
        setThemeState(s.theme);
      } else {
        setThemeState('dark');
      }
    }).catch(console.error);
  }, []);

  const resolvedTheme: ResolvedTheme = theme;

  // Apply theme class to document.documentElement
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    if (resolvedTheme === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
      root.setAttribute('data-theme', 'light');
    } else {
      root.classList.remove('light');
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
    }
  }, [resolvedTheme]);

  const setTheme = (mode: ThemeMode) => {
    const finalMode: ThemeMode = mode === 'light' ? 'light' : 'dark';
    setThemeState(finalMode);
    bridge.getSettings().then((current) => {
      if (current) {
        bridge.saveSettings({ ...current, theme: finalMode }).catch(console.error);
      }
    }).catch(console.error);
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
