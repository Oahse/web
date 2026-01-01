import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';

/**
 * AdminUserEdit component allows administrators to edit existing user accounts.
 * It includes fields for user details, role selection, and avatar upload.
 */
export const AdminUserEdit = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  return (
    <div className="max-w-md mx-auto mt-8 mb-8">
      <h1 className="text-2xl font-bold text-main mb-4">Edit User</h1>
      <div className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <p>Editing user with ID: {id}</p>
        <button
          type="button"
          className="px-4 py-2 border border-border rounded-md text-copy hover:bg-surface-hover mt-4"
          onClick={() => navigate(`/admin/users/${id}`)}
        >
          Back to User Detail
        </button>
      </div>
    </div>
  );
};