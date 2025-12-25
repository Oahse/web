import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Textarea } from '../../components/forms/Textarea'; // Assuming a Textarea component exists

export const AdminBlogCategoryForm = () => {
  const { categoryId } = useParams<{ categoryId?: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<BlogCategoryCreate | BlogCategoryUpdate>({
    name: '',
    slug: '',
    description: '',
  });
  const [isEditMode, setIsEditMode] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // API hooks for fetching and submitting
  const { data: fetchedCategory, loading, error, execute: fetchCategory } = useApi<BlogCategoryResponse>();
  const { execute: submitCategory } = useApi<BlogCategoryResponse>();

  useEffect(() => {
    if (categoryId) {
      setIsEditMode(true);
      fetchCategory(() => AdminAPI.getBlogCategoryBySlug(categoryId)); // Assuming categoryId is a slug here, adjust if it's an actual ID
    } else {
      setIsEditMode(false);
    }
  }, [categoryId, fetchCategory]);

  useEffect(() => {
    if (fetchedCategory) {
      setFormData({
        name: fetchedCategory.data.name,
        slug: fetchedCategory.data.slug,
        description: fetchedCategory.data.description || '',
      });
    }
  }, [fetchedCategory]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
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
      if (isEditMode && categoryId) {
        response = await submitCategory(() => AdminAPI.updateBlogCategory(fetchedCategory?.data?.id || categoryId, formData)); // Use fetched ID for update
        toast.success('Blog category updated successfully!');
      } else {
        response = await submitCategory(() => AdminAPI.createBlogCategory(formData));
        toast.success('Blog category created successfully!');
      }
      navigate('/admin/blog/categories'); // Redirect to category list
    } catch (err: any) {
      toast.error(`Failed to ${isEditMode ? 'update' : 'create'} category: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [isEditMode, categoryId, formData, navigate, submitCategory, fetchedCategory]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={() => fetchCategory(() => AdminAPI.getBlogCategoryBySlug(categoryId!))} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">{isEditMode ? 'Edit' : 'Create'} Blog Category</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 gap-4 mb-6">
          <Input
            label="Category Name"
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
          <Textarea
            label="Description"
            name="description"
            value={formData.description || ''}
            onChange={handleChange}
            rows={4}
          />
        </div>

        <div className="mt-6 text-right">
          <button
            type="button"
            className="btn btn-secondary mr-2"
            onClick={() => navigate('/admin/blog/categories')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? <LoadingSpinner size="sm" /> : (isEditMode ? 'Update Category' : 'Create Category')}
          </button>
        </div>
      </form>
    </div>
  );
};
