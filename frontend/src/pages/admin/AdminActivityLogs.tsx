import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ActivityLog } from '../../types'; // Assuming ActivityLog type exists
import { Input } from '../../components/forms/Input';
import { Select } from '../../components/forms/Select';

export const AdminActivityLogs = () => {
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    userId: '',
    actionType: '',
    dateFrom: '',
    dateTo: '',
    search: '',
  });

  const { data: fetchedLogs, loading, error, execute: fetchLogs } = useApi<{
    total: number;
    page: number;
    limit: number;
    data: ActivityLog[];
  }>();

  const loadLogs = useCallback(async () => {
    await fetchLogs(() => AdminAPI.getAuditLogs({ // Re-using getAuditLogs, assuming it can handle activity logs
      page: currentPage,
      limit: 10, // Or a suitable default limit
      user_id: filters.userId || undefined,
      action: filters.actionType || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      search: filters.search || undefined, // Assuming a general search for description/metadata
    }));
  }, [currentPage, filters, fetchLogs]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  useEffect(() => {
    if (fetchedLogs) {
      setActivityLogs(fetchedLogs.data);
      setTotalPages(Math.ceil(fetchedLogs.total / fetchedLogs.limit));
    }
  }, [fetchedLogs]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
    setCurrentPage(1); // Reset to first page on new filter
  }, []);

  if (loading && !fetchedLogs) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={loadLogs} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Activity Logs</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Input
          label="User ID"
          name="userId"
          value={filters.userId}
          onChange={handleFilterChange}
          placeholder="Filter by User ID"
        />
        <Input
          label="Action Type"
          name="actionType"
          value={filters.actionType}
          onChange={handleFilterChange}
          placeholder="Filter by Action Type"
        />
        <Input
          label="Date From"
          name="dateFrom"
          type="date"
          value={filters.dateFrom}
          onChange={handleFilterChange}
        />
        <Input
          label="Date To"
          name="dateTo"
          type="date"
          value={filters.dateTo}
          onChange={handleFilterChange}
        />
        <Input
          label="Search"
          name="search"
          value={filters.search}
          onChange={handleFilterChange}
          placeholder="Search description/metadata"
          className="md:col-span-2"
        />
      </div>

      {!activityLogs || activityLogs.length === 0 ? (
        <div className="text-center text-copy-light p-8">No activity logs found.</div>
      ) : (
        <div className="overflow-x-auto bg-surface rounded-lg shadow-sm">
          <table className="table w-full">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User ID</th>
                <th>Action Type</th>
                <th>Description</th>
                <th>Metadata</th>
              </tr>
            </thead>
            <tbody>
              {activityLogs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                  <td>{log.user_id || 'N/A'}</td>
                  <td>{log.action_type}</td>
                  <td>{log.description}</td>
                  <td>
                    <pre className="text-xs max-w-xs overflow-auto">
                      {log.metadata ? JSON.stringify(log.metadata, null, 2) : 'N/A'}
                    </pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex justify-center mt-4">
          <div className="join">
            <button className="join-item btn" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>«</button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button key={page} className={`join-item btn ${currentPage === page ? 'btn-active' : ''}`} onClick={() => handlePageChange(page)}>{page}</button>
            ))}
            <button className="join-item btn" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>»</button>
          </div>
        </div>
      )}
    </div>
  );
};
