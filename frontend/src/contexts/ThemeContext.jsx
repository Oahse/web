import { useEffect, useState, createContext, useCallback, useContext } from 'react';
import { useAuth } from './AuthContext';
import { themeUtils, defaultTheme } from '../lib/theme';

export const ThemeContext = createContext(undefined);

export const ThemeProvider = ({ children }) => {
  const { user, updateUserPreferences } = useAuth();

  // Initialize theme from user preferences, localStorage, or default
  const [theme, setThemeState] = useState(() => {
    if (user?.preferences?.theme) {
      return user.preferences.theme;
    }
    return themeUtils.loadThemePreference();
  });

  const [currentTheme, setCurrentTheme] = useState(() =>
    themeUtils.getEffectiveTheme(theme)
  );

  const [config, setConfig] = useState(defaultTheme);

  // ✅ Stable function to apply theme
  const applyTheme = useCallback(
    (newTheme) => {
      themeUtils.applyTheme(newTheme);
      const effectiveTheme = themeUtils.getEffectiveTheme(newTheme);
      setCurrentTheme(effectiveTheme);

      // Save to localStorage
      themeUtils.saveThemePreference(newTheme);

      // Dispatch custom event for other components to listen
      window.dispatchEvent(
        new CustomEvent('themeChange', {
          detail: { theme: newTheme, effectiveTheme },
        })
      );
    },
    []
  );

  // ✅ Handle theme changes
  useEffect(() => {
    applyTheme(theme);

    // Watch for system theme changes if using system theme
    if (theme === 'system') {
      const cleanup = themeUtils.watchSystemTheme((isDark) => {
        const effective = isDark ? 'dark' : 'light';
        setCurrentTheme(effective);
        themeUtils.applyTheme('system');
      });
      return cleanup;
    }
  }, [theme, applyTheme]);

  // ✅ Sync with user preferences
  useEffect(() => {
    if (user?.preferences?.theme && user.preferences.theme !== theme) {
      setThemeState(user.preferences.theme);
    }
  }, [user?.preferences?.theme, theme]);

  // ✅ Update theme preference
  const setTheme = async (newTheme) => {
    setThemeState(newTheme);

    // Update user preferences if authenticated
    if (user) {
      try {
        await updateUserPreferences({ theme: newTheme });
      } catch (error) {
        console.error('Failed to update theme preference:', error);
      }
    }
  };

  // ✅ Update theme configuration (colors, spacing, etc.)
  const updateThemeConfig = (newConfig) => {
    setConfig((prev) => ({ ...prev, ...newConfig }));
  };

  const value = {
    theme,
    currentTheme,
    config,
    setTheme,
    updateThemeConfig,
    isSystemTheme: theme === 'system',
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme error: must be used within a ThemeProvider');
  }
  return context;
};