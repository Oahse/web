import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ConfirmationModal } from '../../components/ui/ConfirmationModal';
import { toast } from 'react-hot-toast';
import { CommentResponse } from '../../types';
import { Link } from 'react-router-dom';
import { SkeletonTable } from '../../components/ui/SkeletonTable';

export const AdminComments = () => {
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterApproved, setFilterApproved] = useState<boolean | undefined>(undefined);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [commentToDelete, setCommentToDelete] = useState<string | null>(null);

  // Assuming a new API method in AdminAPI to get all comments
  // This will need to be added to frontend/src/apis/admin.ts later
  const { data: fetchedComments, loading, error, execute: fetchComments } = useApi<{
    total: number;
    page: number;
    limit: number;
    data: CommentResponse[];
  }>();

  const loadComments = useCallback(async () => {
    // AdminAPI.getAllComments will be implemented later
    await fetchComments(() => AdminAPI.getAllComments({
      page: currentPage,
      limit: 10,
      is_approved: filterApproved,
    }));
  }, [currentPage, filterApproved, fetchComments]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  useEffect(() => {
    if (fetchedComments) {
      setComments(fetchedComments.data);
      setTotalPages(Math.ceil(fetchedComments.total / fetchedComments.limit));
    }
  }, [fetchedComments]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleFilterApprovedChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setFilterApproved(value === 'true' ? true : value === 'false' ? false : undefined);
    setCurrentPage(1);
  };

  const handleToggleApproved = useCallback(async (comment: CommentResponse) => {
    setLoadingAction(comment.id);
    try {
      // AdminAPI.updateComment will be implemented later
      await AdminAPI.updateComment(comment.id, { is_approved: !comment.is_approved });
      toast.success(`Comment ${comment.is_approved ? 'unapproved' : 'approved'} successfully!`);
      loadComments();
    } catch (err: any) {
      toast.error(`Failed to toggle approval status: ${err.message || 'Unknown error'}`);
    } finally {
      setLoadingAction(null);
    }
  }, [loadComments]);

  const handleDeleteComment = useCallback(async (commentId: string) => {
    setCommentToDelete(commentId);
    setShowDeleteModal(true);
  }, []);

  const confirmDeleteComment = useCallback(async () => {
    if (!commentToDelete) return;
    
    setLoadingAction(commentToDelete);
    try {
      // AdminAPI.deleteComment will be implemented later
      await AdminAPI.deleteComment(commentToDelete);
      toast.success('Comment deleted successfully!');
      loadComments();
    } catch (err: any) {
      toast.error(`Failed to delete comment: ${err.message || 'Unknown error'}`);
    } finally {
      setLoadingAction(null);
      setShowDeleteModal(false);
      setCommentToDelete(null);
    }
  }, [commentToDelete, loadComments]);

  // Early returns after all hooks
  if (loading && !fetchedComments) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-main mb-2">Comments Management</h1>
          <p className="text-copy-lighter">Moderate and manage user comments.</p>
        </div>
        <SkeletonTable rows={5} columns={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={loadComments} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Comment Management</h1>

      <div className="flex justify-between items-center mb-4">
        <select
          className="select select-bordered"
          value={filterApproved === undefined ? 'all' : filterApproved.toString()}
          onChange={handleFilterApprovedChange}
        >
          <option value="all">All Statuses</option>
          <option value="true">Approved</option>
          <option value="false">Pending Approval</option>
        </select>
      </div>

      {!comments || comments.length === 0 ? (
        <div className="text-center text-copy-light p-8">No comments found.</div>
      ) : (
        <div className="overflow-x-auto bg-surface rounded-lg shadow-sm">
          <table className="table w-full">
            <thead>
              <tr>
                <th>Post Title</th>
                <th>Author</th>
                <th>Content</th>
                <th>Approved</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {comments.map((comment) => (
                <tr key={comment.id}>
                  <td>
                    {/* Post reference removed */}
                    {comment.post_id || 'N/A'}
                  </td>
                  <td>{comment.author?.full_name || comment.author?.firstname || 'N/A'}</td>
                  <td>{comment.content.substring(0, 100)}...</td>
                  <td>{comment.is_approved ? 'Yes' : 'No'}</td>
                  <td>{new Date(comment.created_at).toLocaleString()}</td>
                  <td className="flex space-x-2">
                    <button
                      className={`btn btn-sm ${comment.is_approved ? 'btn-warning' : 'btn-success'}`}
                      onClick={() => handleToggleApproved(comment)}
                      disabled={loadingAction === comment.id}
                    >
                      {loadingAction === comment.id ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        comment.is_approved ? 'Unapprove' : 'Approve'
                      )}
                    </button>
                    <button
                      className="btn btn-sm btn-error"
                      onClick={() => handleDeleteComment(comment.id)}
                      disabled={loadingAction === comment.id}
                    >
                      {loadingAction === comment.id ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        'Delete'
                      )}
                    </button>
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

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setCommentToDelete(null);
        }}
        onConfirm={confirmDeleteComment}
        title="Delete Comment"
        message="Are you sure you want to delete this comment? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        loading={loadingAction === commentToDelete}
      />
    </div>
  );
};
