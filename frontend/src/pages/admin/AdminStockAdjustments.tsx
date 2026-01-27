import React, { useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, ClockIcon, PlusIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';

export const AdminStockAdjustments = () => {
  const { inventoryId } = useParams<{ inventoryId?: string }>();
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [userId, setUserId] = useState('');
  const [reason, setReason] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const apiCall = useCallback((page: number, limit: number) => {
    if (inventoryId && inventoryId !== 'all') {
      return AdminAPI.getStockAdjustments(inventoryId);
    } else {
      return AdminAPI.getAllStockAdjustments();
    }
  }, [inventoryId]);

  const {
    data: adjustments,
    loading: adjustmentsLoading,
    error: adjustmentsError,
    execute: fetchAdjustments,
    page: currentPage,
    limit: itemsPerPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedSearchTerm(searchTerm);
    setLocalCurrentPage(1); // Reset to first page when searching
  };

  if (adjustmentsError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={adjustmentsError}
          onRetry={() => fetchAdjustments()}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  // Local pagination state
  const [localCurrentPage, setLocalCurrentPage] = useState(1);
  const itemsPerPageLocal = 10;

  // Filter adjustments based on search and filters
  const filteredAdjustments = adjustments.filter(adjustment => {
    const matchesSearch = !submittedSearchTerm || 
      adjustment.reason?.toLowerCase().includes(submittedSearchTerm.toLowerCase()) ||
      adjustment.notes?.toLowerCase().includes(submittedSearchTerm.toLowerCase()) ||
      adjustment.inventory_id?.toLowerCase().includes(submittedSearchTerm.toLowerCase());
    
    const matchesUserId = !userId || adjustment.adjusted_by_user_id?.includes(userId);
    const matchesReason = !reason || adjustment.reason?.toLowerCase().includes(reason.toLowerCase());
    
    const adjustmentDate = new Date(adjustment.created_at);
    const matchesDateFrom = !dateFrom || adjustmentDate >= new Date(dateFrom);
    const matchesDateTo = !dateTo || adjustmentDate <= new Date(dateTo);
    
    return matchesSearch && matchesUserId && matchesReason && matchesDateFrom && matchesDateTo;
  });

  // Calculate pagination for filtered results
  const totalFilteredPages = Math.ceil(filteredAdjustments.length / itemsPerPageLocal);
  const startIndex = (localCurrentPage - 1) * itemsPerPageLocal;
  const endIndex = Math.min(startIndex + itemsPerPageLocal, filteredAdjustments.length);
  const paginatedAdjustments = filteredAdjustments.slice(startIndex, endIndex);

  return (
    <div>
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold text-main mb-2 md:mb-0">
          Stock Adjustments {inventoryId ? `for Item ${inventoryId}` : ''}
        </h1>
        <Link to="/admin/inventory/adjustments/new" className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-md transition-colors">
          <PlusIcon size={18} className="mr-2" />
          New Adjustment
        </Link>
      </div>

      {/* Filters and search */}
      <div className="bg-surface rounded-lg shadow-sm p-4 mb-6 border border-border-light">
        <form onSubmit={handleSearch}>
          <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-4">
            <div className="flex-grow">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Search adjustments by reason, notes, or inventory ID..." 
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                />
                <SearchIcon size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button type="button" onClick={() => setShowMoreFilters(!showMoreFilters)} className="flex items-center px-3 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                <FilterIcon size={18} className="mr-2" />
                More Filters
              </button>
              <button type="submit" className="flex items-center px-3 py-2 bg-primary text-white rounded-md hover:bg-primary-dark">
                <SearchIcon size={18} className="mr-2" />
                Search
              </button>
            </div>
          </div>
        </form>
        {showMoreFilters && (
          <div className="mt-4 pt-4 border-t border-border-light">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="text-sm text-copy-light mb-1 block">User ID</label>
                <input 
                  type="text" 
                  placeholder="Adjusted by user ID" 
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={userId} 
                  onChange={e => setUserId(e.target.value)} 
                />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Reason</label>
                <input 
                  type="text" 
                  placeholder="Adjustment reason" 
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={reason} 
                  onChange={e => setReason(e.target.value)} 
                />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Date From</label>
                <input 
                  type="date" 
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={dateFrom} 
                  onChange={e => setDateFrom(e.target.value)} 
                />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Date To</label>
                <input 
                  type="date" 
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={dateTo} 
                  onChange={e => setDateTo(e.target.value)} 
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Adjustments table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        <ResponsiveTable
          data={paginatedAdjustments || []}
          loading={adjustmentsLoading}
          keyExtractor={(adjustment) => adjustment.id}
          emptyMessage="No stock adjustments found"
          columns={[
            {
              key: 'adjustment',
              label: 'Adjustment',
              mobileLabel: 'Adjustment',
              render: (adjustment) => (
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mr-3">
                    <ClockIcon size={18} className="text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-main">
                      {adjustment.quantity_change > 0 ? '+' : ''}{adjustment.quantity_change}
                    </p>
                    <p className="text-xs text-copy-light">
                      {new Date(adjustment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ),
            },
            {
              key: 'inventory',
              label: 'Inventory ID',
              hideOnMobile: true,
              render: (adjustment) => (
                <span className="text-copy-light font-mono text-sm">{adjustment.inventory_id}</span>
              ),
            },
            {
              key: 'reason',
              label: 'Reason',
              render: (adjustment) => (
                <span className="text-copy-light">{adjustment.reason || 'No reason provided'}</span>
              ),
            },
            {
              key: 'user',
              label: 'Adjusted By',
              hideOnMobile: true,
              render: (adjustment) => (
                <span className="text-copy-light">{adjustment.adjusted_by_user_id || 'System'}</span>
              ),
            },
            {
              key: 'notes',
              label: 'Notes',
              hideOnMobile: true,
              render: (adjustment) => (
                <span className="text-copy-light">{adjustment.notes || 'No notes'}</span>
              ),
            },
            {
              key: 'timestamp',
              label: 'Time',
              render: (adjustment) => (
                <span className="text-copy-light text-sm">
                  {new Date(adjustment.created_at).toLocaleTimeString()}
                </span>
              ),
            },
          ]}
        />
      </div>

      {/* Pagination */}
      {totalFilteredPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-copy-light">
            Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
            <span className="font-medium">{Math.min(endIndex, filteredAdjustments.length)}</span> of{' '}
            <span className="font-medium">{filteredAdjustments.length}</span> adjustments
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setLocalCurrentPage(localCurrentPage - 1)}
              disabled={localCurrentPage === 1}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex items-center gap-1">
              {[...Array(totalFilteredPages)].map((_, pageNum) => (
                <button
                  key={pageNum + 1}
                  onClick={() => setLocalCurrentPage(pageNum + 1)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    localCurrentPage === pageNum + 1
                      ? 'bg-primary text-white'
                      : 'border border-border text-copy hover:bg-surface-hover'
                  }`}
                >
                  {pageNum + 1}
                </button>
              ))}
            </div>
            
            <button
              onClick={() => setLocalCurrentPage(localCurrentPage + 1)}
              disabled={localCurrentPage === totalFilteredPages}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default AdminStockAdjustments;