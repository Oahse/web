import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogCategoryResponse, BlogTagResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Textarea } from '../../components/forms/Textarea';
import { Select } from '../../components/forms/Select';
import { Checkbox } from '../../components/forms/Checkbox'; // Assuming a Checkbox component exists

// Helper to create a slug from a title
const createSlug = (title: string) => {
  return title.toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove non-alphanumeric characters except spaces and hyphens
    .replace(/\s+/g, '-')       // Replace spaces with hyphens
    .replace(/^-+|-+$/g, '');   // Remove leading/trailing hyphens
};

export const AdminBlogPostForm = () => {
  const { postId } = useParams<{ postId?: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<BlogPostCreate | BlogPostUpdate>({
    title: '',
    slug: '',
    content: '',
    excerpt: '',
    category_id: undefined,
    image_url: '',
    is_published: false,
    seo_title: '',
    seo_description: '',
    seo_keywords: '',
    tags: [],
  });
  const [isEditMode, setIsEditMode] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [categories, setCategories] = useState<BlogCategoryResponse[]>([]);
  const [availableTags, setAvailableTags] = useState<BlogTagResponse[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]); // Storing tag names/slugs

  // API hooks
  const { data: fetchedPost, loading: loadingPost, error: postError, execute: fetchPost } = useApi<BlogPostResponse>();
  const { data: fetchedCategories, loading: loadingCategories, error: categoriesError, execute: fetchCategories } = useApi<BlogCategoryResponse[]>();
  const { data: fetchedTags, loading: loadingTags, error: tagsError, execute: fetchTags } = useApi<BlogTagResponse[]>();
  const { execute: submitBlogPost } = useApi<BlogPostResponse>();

  // Fetch initial data (post, categories, tags)
  useEffect(() => {
    if (postId) {
      setIsEditMode(true);
      fetchPost(() => AdminAPI.getBlogPostBySlug(postId)); // Assuming postId can be a slug for fetching
    } else {
      setIsEditMode(false);
    }
    fetchCategories(AdminAPI.getBlogCategories);
    fetchTags(AdminAPI.getBlogTags);
  }, [postId, fetchPost, fetchCategories, fetchTags]);

  // Populate form data when fetchedPost or fetchedCategories/fetchedTags change
  useEffect(() => {
    if (fetchedPost && isEditMode) {
      const post = fetchedPost.data;
      setFormData({
        title: post.title,
        slug: post.slug,
        content: post.content,
        excerpt: post.excerpt || '',
        category_id: post.category?.id,
        image_url: post.image_url || '',
        is_published: post.is_published,
        seo_title: post.seo_title || '',
        seo_description: post.seo_description || '',
        seo_keywords: post.seo_keywords || '',
        tags: post.tags?.map(tag => tag.name) || [], // Map fetched tags to names
      });
      setSelectedTags(post.tags?.map(tag => tag.name) || []);
    }
  }, [fetchedPost, isEditMode]);

  useEffect(() => {
    if (fetchedCategories) {
      setCategories(fetchedCategories.data);
    }
  }, [fetchedCategories]);

  useEffect(() => {
    if (fetchedTags) {
      setAvailableTags(fetchedTags.data);
    }
  }, [fetchedTags]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    let newValue: string | boolean | undefined;

    if (type === 'checkbox') {
      newValue = (e.target as HTMLInputElement).checked;
    } else if (name === 'title' && !isEditMode) { // Auto-generate slug only for new posts
      setFormData(prev => ({
        ...prev,
        title: value,
        slug: createSlug(value),
      }));
      return;
    } else {
      newValue = value;
    }

    setFormData(prev => ({
      ...prev,
      [name]: newValue,
    }));
  }, [isEditMode]);

  const handleTagChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const options = Array.from(e.target.selectedOptions, option => option.value);
    setSelectedTags(options);
    setFormData(prev => ({
      ...prev,
      tags: options,
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let response: any;
      const finalFormData = { ...formData };
      
      // Ensure category_id is a string UUID if present, otherwise null
      finalFormData.category_id = finalFormData.category_id ? String(finalFormData.category_id) : undefined;
      
      // If slug is empty in create mode, generate from title
      if (!isEditMode && !finalFormData.slug && finalFormData.title) {
        finalFormData.slug = createSlug(finalFormData.title);
      } else if (isEditMode && finalFormData.slug === "") {
        // Ensure slug is not empty on update if it was populated
        finalFormData.slug = createSlug(finalFormData.title || '');
      }

      if (isEditMode && postId) {
        response = await submitBlogPost(() => AdminAPI.updateBlogPost(postId, finalFormData as BlogPostUpdate));
        toast.success('Blog post updated successfully!');
      } else {
        response = await submitBlogPost(() => AdminAPI.createBlogPost(finalFormData as BlogPostCreate));
        toast.success('Blog post created successfully!');
      }
      navigate('/admin/blog/posts'); // Redirect to blog post list
    } catch (err: any) {
      toast.error(`Failed to ${isEditMode ? 'update' : 'create'} post: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [isEditMode, postId, formData, navigate, submitBlogPost]);

  const categoryOptions = useMemo(() => {
    return categories.map(cat => ({ value: cat.id, label: cat.name }));
  }, [categories]);

  const tagOptions = useMemo(() => {
    return availableTags.map(tag => ({ value: tag.name, label: tag.name }));
  }, [availableTags]);

  if (loadingPost || loadingCategories || loadingTags) {
    return <LoadingSpinner />;
  }

  if (postError || categoriesError || tagsError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={postError || categoriesError || tagsError}
          onRetry={() => {
            if (postId) fetchPost(() => AdminAPI.getBlogPostBySlug(postId));
            fetchCategories(AdminAPI.getBlogCategories);
            fetchTags(AdminAPI.getBlogTags);
          }}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">{isEditMode ? 'Edit' : 'Create'} Blog Post</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Input
            label="Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
          <Input
            label="Slug"
            name="slug"
            value={formData.slug || ''}
            onChange={handleChange}
            placeholder="Auto-generated from title"
            disabled={isEditMode} // Disable slug editing for existing posts
          />
          <Select
            label="Category"
            name="category_id"
            value={formData.category_id || ''}
            onChange={handleChange}
            options={[{ value: '', label: 'Select Category' }, ...categoryOptions]}
            required
          />
          <Input
            label="Image URL"
            name="image_url"
            value={formData.image_url || ''}
            onChange={handleChange}
            placeholder="URL to featured image"
          />
          <Textarea
            label="Excerpt"
            name="excerpt"
            value={formData.excerpt || ''}
            onChange={handleChange}
            rows={2}
            className="md:col-span-2"
          />
          <Textarea
            label="Content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            rows={10}
            required
            className="md:col-span-2"
          />
          <Checkbox
            label="Published"
            name="is_published"
            checked={formData.is_published}
            onChange={handleChange}
          />
        </div>

        {/* Tags Multi-select */}
        <div className="mb-6">
          <label htmlFor="tags" className="block text-lg font-medium text-main mb-2">Tags</label>
          <select
            id="tags"
            name="tags"
            multiple
            value={selectedTags}
            onChange={handleTagChange}
            className="select select-bordered w-full"
          >
            {tagOptions.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <p className="text-sm text-copy-light mt-1">Select multiple tags by holding Ctrl/Cmd.</p>
        </div>

        {/* SEO Fields */}
        <div className="border border-border-light p-4 rounded-lg mb-6">
          <h2 className="text-xl font-semibold text-main mb-4">SEO Optimization</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="SEO Title"
              name="seo_title"
              value={formData.seo_title || ''}
              onChange={handleChange}
              placeholder="Meta title for search engines"
            />
            <Input
              label="SEO Keywords"
              name="seo_keywords"
              value={formData.seo_keywords || ''}
              onChange={handleChange}
              placeholder="Comma-separated keywords"
            />
            <Textarea
              label="SEO Description"
              name="seo_description"
              value={formData.seo_description || ''}
              onChange={handleChange}
              rows={3}
              className="md:col-span-2"
            />
          </div>
        </div>

        <div className="mt-6 text-right">
          <button
            type="button"
            className="btn btn-secondary mr-2"
            onClick={() => navigate('/admin/blog/posts')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? <LoadingSpinner size="sm" /> : (isEditMode ? 'Update Post' : 'Create Post')}
          </button>
        </div>
      </form>
    </div>
  );
};
