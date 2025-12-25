import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { BlogTagCreate, BlogTagUpdate, BlogTagResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';

export const AdminBlogTagForm = () => {
  const { tagId } = useParams<{ tagId?: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<BlogTagCreate | BlogTagUpdate>({
    name: '',
    slug: '',
  });
  const [isEditMode, setIsEditMode] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // API hooks for fetching and submitting
  const { data: fetchedTag, loading, error, execute: fetchTag } = useApi<BlogTagResponse>();
  const { execute: submitTag } = useApi<BlogTagResponse>();

  useEffect(() => {
    if (tagId) {
      setIsEditMode(true);
      fetchTag(() => AdminAPI.getBlogTagBySlug(tagId)); // Assuming tagId is a slug here, adjust if it's an actual ID
    } else {
      setIsEditMode(false);
    }
  }, [tagId, fetchTag]);

  useEffect(() => {
    if (fetchedTag) {
      setFormData({
        name: fetchedTag.data.name,
        slug: fetchedTag.data.slug,
      });
    }
  }, [fetchedTag]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let response: any;
      if (isEditMode && tagId) {
        response = await submitTag(() => AdminAPI.updateBlogTag(fetchedTag?.data?.id || tagId, formData)); // Use fetched ID for update
        toast.success('Blog tag updated successfully!');
      } else {
        response = await submitTag(() => AdminAPI.createBlogTag(formData));
        toast.success('Blog tag created successfully!');
      }
      navigate('/admin/blog/tags'); // Redirect to tag list
    } catch (err: any) {
      toast.error(`Failed to ${isEditMode ? 'update' : 'create'} tag: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [isEditMode, tagId, formData, navigate, submitTag, fetchedTag]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={() => fetchTag(() => AdminAPI.getBlogTagBySlug(tagId!))} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">{isEditMode ? 'Edit' : 'Create'} Blog Tag</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 gap-4 mb-6">
          <Input
            label="Tag Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
          <Input
            label="Slug"
            name="slug"
            value={formData.slug || ''}
            onChange={handleChange}
            placeholder="Auto-generated from name if left empty"
          />
        </div>

        <div className="mt-6 text-right">
          <button
            type="button"
            className="btn btn-secondary mr-2"
            onClick={() => navigate('/admin/blog/tags')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? <LoadingSpinner size="sm" /> : (isEditMode ? 'Update Tag' : 'Create Tag')}
          </button>
        </div>
      </form>
    </div>
  );
};
