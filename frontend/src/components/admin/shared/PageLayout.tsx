import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface AdminPageLayoutProps {
  title: string;
  subtitle?: string;
  description?: string;
  icon?: LucideIcon;
  actions?: React.ReactNode;
  breadcrumbs?: Array<{
    label: string;
    href?: string;
  }>;
  children: React.ReactNode;
  className?: string;
}

export const AdminPageLayout: React.FC<AdminPageLayoutProps> = ({
  title,
  subtitle,
  description,
  icon: Icon,
  actions,
  breadcrumbs,
  children,
  className = ''
}) => {
  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            {/* Breadcrumbs */}
            {breadcrumbs && breadcrumbs.length > 0 && (
              <nav className="flex mb-4" aria-label="Breadcrumb">
                <ol className="flex items-center space-x-2">
                  {breadcrumbs.map((breadcrumb, index) => (
                    <li key={index} className="flex items-center">
                      {index > 0 && (
                        <svg
                          className="flex-shrink-0 h-5 w-5 text-gray-400 dark:text-gray-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                      {breadcrumb.href ? (
                        <a
                          href={breadcrumb.href}
                          className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                        >
                          {breadcrumb.label}
                        </a>
                      ) : (
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {breadcrumb.label}
                        </span>
                      )}
                    </li>
                  ))}
                </ol>
              </nav>
            )}

            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center space-x-4">
                {Icon && (
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400">
                      <Icon className="h-6 w-6" />
                    </div>
                  </div>
                )}
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
                  {subtitle && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>
                  )}
                  {description && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{description}</p>
                  )}
                </div>
              </div>
              
              {actions && (
                <div className="flex items-center space-x-3">
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    {actions}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
    </div>
  );
};

export default AdminPageLayout;
