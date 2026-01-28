import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { MobileSearch } from './MobileSearch';
import { MobileCategories } from './MobileCategories';
import { useTheme } from '../../store/ThemeContext';

export const Layout = ({
  children,
  className = '',
  showHeader = true,
  showFooter = true,
  headerProps = {},
  footerProps = {},
}) => {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isCategoriesOpen, setIsCategoriesOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  useTheme();

  // Handle scroll detection for header styling
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menus when clicking outside or pressing Escape
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsSearchOpen(false);
        setIsCategoriesOpen(false);
      }
    };

    const handleClickOutside = (event) => {
      if (!event.target.closest('[data-mobile-menu]')) {
        setIsSearchOpen(false);
        setIsCategoriesOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  // Prevent body scroll when mobile menus are open
  useEffect(() => {
    document.body.style.overflow = isSearchOpen || isCategoriesOpen ? 'hidden' : 'unset';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isSearchOpen, isCategoriesOpen]);

  return (
    <div
      className={`min-h-screen flex flex-col bg-background text-copy transition-colors duration-200 ease-in-out ${className}`}
      data-mobile-menu
    >
      {showHeader && (
        <Header
          onSearchClick={(e) => {
            e.preventDefault();
            setIsSearchOpen(true);
          }}
          onCategoriesClick={(e) => {
            e.preventDefault();
            setIsCategoriesOpen(true);
          }}
          isScrolled={isScrolled}
          {...headerProps}
        />
      )}

      <main
        className={`flex-1 w-full transition-all duration-200 ease-in-out ${
          showHeader ? 'pt-0' : ''
        }`}
      >
        {children}
      </main>

      {showFooter && <Footer {...footerProps} />}

      {/* Mobile overlays */}
      <MobileSearch isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <MobileCategories isOpen={isCategoriesOpen} onClose={() => setIsCategoriesOpen(false)} />

      {(isSearchOpen || isCategoriesOpen) && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => {
            setIsSearchOpen(false);
            setIsCategoriesOpen(false);
          }}
          aria-hidden="true"
        />
      )}
    </div>
  );
};

// Specialized layout variants
export const AdminLayout = ({ children, ...props }) => (
  <Layout showHeader={false} showFooter={false} className="bg-surface-elevated" {...props}>
    {children}
  </Layout>
);

export const AuthLayout = ({ children, ...props }) => (
  <Layout showHeader={false} showFooter={false} className="bg-background" {...props}>
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  </Layout>
);

export const MinimalLayout = ({ children, ...props }) => (
  <Layout showFooter={false} headerProps={{ minimal: true }} {...props}>
    {children}
  </Layout>
);
