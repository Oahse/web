import React from 'react';

interface Column<T> {
  key: string;
  label: string;
  render: (item: T) => React.ReactNode;
  mobileLabel?: string;
  hideOnMobile?: boolean;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
}

export function ResponsiveTable<T>({
  data,
  columns,
  keyExtractor,
  loading = false,
  emptyMessage = 'No data available',
  onRowClick,
}: ResponsiveTableProps<T>) {
  if (loading) {
    return (
      <div className="space-y-4">
        {/* Desktop skeleton */}
        <div className="hidden md:block">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead className="bg-surface-hover">
                <tr>
                  {columns.map((col, idx) => (
                    <th key={idx} className="py-3 px-4 text-left font-medium">
                      <div className="w-16 h-4 bg-surface-hover rounded animate-pulse" data-testid="desktop-skeleton-header-cell"></div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...Array(5)].map((_, index) => (
                  <tr key={index} className="border-t border-border-light">
                    {columns.map((_, colIdx) => (
                      <td key={colIdx} className="py-3 px-4">
                        <div className="w-full h-4 bg-surface-hover rounded animate-pulse" data-testid="desktop-skeleton-data-cell"></div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mobile skeleton */}
        <div className="md:hidden space-y-3 p-4">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="bg-surface rounded-lg p-4 border border-border-light animate-pulse" data-testid="mobile-skeleton-row">
              <div className="space-y-2">
                <div className="w-3/4 h-4 bg-surface-hover rounded"></div>
                <div className="w-1/2 h-3 bg-surface-hover rounded"></div>
                <div className="w-full h-3 bg-surface-hover rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 px-4 text-copy-light">
        {emptyMessage}
      </div>
    );
  }

  return (
    <>
      {/* Desktop Table View */}
      <div className="hidden md:block">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-surface-hover">
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx} className="py-3 px-4 text-left font-medium text-main text-sm whitespace-nowrap">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  className={`border-t border-border-light hover:bg-surface-hover ${
                    onRowClick ? 'cursor-pointer' : ''
                  }`}
                  onClick={() => onRowClick?.(item)}
                >
                  {columns.map((col, idx) => (
                    <td key={idx} className="py-3 px-4 text-sm">
                      {col.render(item)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile List View */}
      <div className="md:hidden space-y-3 p-4">
        {data.map((item) => (
          <div
            key={keyExtractor(item)}
            className={`bg-surface rounded-lg p-4 border border-border-light ${
              onRowClick ? 'cursor-pointer active:bg-surface-hover' : ''
            }`}
            onClick={() => onRowClick?.(item)}
          >
            <div className="space-y-3">
              {columns
                .filter((col) => !col.hideOnMobile)
                .map((col, idx) => (
                  <div key={idx} className="flex justify-between items-start">
                    <span className="text-sm font-medium text-copy-light mr-2 flex-shrink-0">
                      {col.mobileLabel || col.label}:
                    </span>
                    <span className="text-sm text-main text-right flex-1 min-w-0">
                      {col.render(item)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
