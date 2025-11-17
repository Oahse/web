// -----------------------------
// 🎨 Default Theme Definition
// -----------------------------
export const defaultTheme = {
  mode: 'system',
  colors: {
    brand: {
      primary: '#61b482',
      secondary: '#f2c94c',
    },
    semantic: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
    surface: {
      background: '#f8fafc',
      surface: '#ffffff',
      elevated: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
      muted: '#94a3b8',
    },
    border: {
      default: '#e2e8f0',
      light: '#f1f5f9',
      strong: '#cbd5e1',
    },
  },
  spacing: {
    xs: '0.5rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  },
};

// -----------------------------
// 🛠️ Theme Utilities
// -----------------------------


export const themeUtils = {
  getEffectiveTheme: (mode) => {
    if (mode === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return mode;
  },
  /**
   * Apply theme to document root
   */
  applyTheme: (mode) => {
    const root = document.documentElement;
    const effective = themeUtils.getEffectiveTheme(mode);
    root.classList.toggle('dark', effective === 'dark');
  },

  /**
   * Save theme preference to localStorage
   */
  saveThemePreference: (mode) => {
    localStorage.setItem('theme-preference', mode);
  },

  /**
   * Load theme preference from localStorage
   */
  loadThemePreference: () => {
    const saved = localStorage.getItem('theme-preference');
    return saved || 'system';
  },

  /**
   * Listen for system theme changes
   */
  watchSystemTheme: (callback) => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => callback(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  },
};

// -----------------------------
// 💅 CSS Utility Classes
// -----------------------------
export const themeClasses = {
  // Interactive states
  interactive: 'transition-all duration-200 ease-in-out',
  hover: 'hover:bg-surface-hover hover:shadow-md',
  active: 'active:bg-surface-active active:scale-95',
  focus: 'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2',
  disabled: 'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',

  // Buttons
  button: {
    base: 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
    primary: 'bg-primary text-white hover:bg-primary-dark focus:ring-primary/50',
    secondary: 'bg-secondary text-white hover:bg-secondary-dark focus:ring-secondary/50',
    outline: 'border border-primary text-primary hover:bg-primary/10 focus:ring-primary/50',
    ghost: 'text-copy hover:bg-surface-hover focus:ring-primary/50',
    danger: 'bg-error text-white hover:bg-error-dark focus:ring-error/50',
  },

  // Form elements
  input: {
    base: 'w-full px-4 py-2 border rounded-md transition-colors focus:outline-none focus:ring-1',
    default: 'border-border bg-surface text-copy focus:border-primary focus:ring-primary',
    error: 'border-error focus:border-error focus:ring-error',
    success: 'border-success focus:border-success focus:ring-success',
  },

  // Cards
  card: {
    base: 'bg-surface rounded-lg border border-border shadow-sm',
    elevated: 'bg-surface-elevated shadow-md',
    interactive: 'hover:shadow-lg hover:border-border-strong transition-all duration-200',
  },

  // Text
  text: {
    heading: 'font-semibold text-copy',
    body: 'text-copy',
    muted: 'text-copy-light',
    small: 'text-sm text-copy-lighter',
  },

  // Layout
  container: 'container mx-auto px-4 max-w-7xl',
  section: 'py-8 md:py-12 lg:py-16',
  grid: {
    responsive: 'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6',
    auto: 'grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-4 md:gap-6',
  },
};

// -----------------------------
// 📱 Breakpoints & Animations
// -----------------------------
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

export const animations = {
  fadeIn: 'animate-in fade-in duration-200',
  slideIn: 'animate-in slide-in-from-bottom-4 duration-300',
  scaleIn: 'animate-in zoom-in-95 duration-200',
  slideOut: 'animate-out slide-out-to-bottom-4 duration-200',
  fadeOut: 'animate-out fade-out duration-150',
};
