import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../hooks/useApi';
import { AdminAPI } from '../apis'; // Using AdminAPI for now
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { BlogPostResponse, CommentCreate, CommentResponse } from '../types';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Textarea } from '../components/forms/Textarea';

export const BlogPost = () => {
  const { slug } = useParams<{ slug?: string }>();
  const { user, isAuthenticated } = useAuth();
  const [commentContent, setCommentContent] = useState('');

  const { data: fetchedPost, loading: loadingPost, error: postError, execute: fetchPost } = useApi<BlogPostResponse>();
  const { data: fetchedComments, loading: loadingComments, error: commentsError, execute: fetchComments } = useApi<CommentResponse[]>();
  const { execute: submitComment } = useApi<CommentResponse>();

  const loadPostAndComments = useCallback(async () => {
    if (slug) {
      await fetchPost(() => AdminAPI.getBlogPostBySlug(slug));
      // Assuming post ID is available after fetching post, or API supports slug for comments
      // For now, let's refetch comments after post to ensure post.id is available
    }
  }, [slug, fetchPost]);

  useEffect(() => {
    loadPostAndComments();
  }, [loadPostAndComments]);

  useEffect(() => {
    if (fetchedPost && fetchedPost.data && fetchedPost.data.id) {
        fetchComments(() => AdminAPI.getCommentsForPost(fetchedPost.data.id));
    }
  }, [fetchedPost, fetchComments]);


  const handleCommentChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCommentContent(e.target.value);
  }, []);

  const handleCommentSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated || !user) {
      toast.error('You must be logged in to comment.');
      return;
    }
    if (!slug || !fetchedPost?.data?.id || !commentContent.trim()) {
      toast.error('Comment cannot be empty.');
      return;
    }

    try {
      const commentData: CommentCreate = {
        blog_post_id: fetchedPost.data.id,
        content: commentContent,
        author_id: user.id, // Assuming user.id is available
      };
      await submitComment(() => AdminAPI.createComment(fetchedPost.data.id, commentData));
      toast.success('Comment posted successfully!');
      setCommentContent('');
      fetchComments(() => AdminAPI.getCommentsForPost(fetchedPost.data.id)); // Refresh comments
    } catch (err: any) {
      toast.error(`Failed to post comment: ${err.message || 'Unknown error'}`);
    }
  }, [slug, fetchedPost, commentContent, isAuthenticated, user, fetchComments, submitComment]);

  if (loadingPost || loadingComments) {
    return <LoadingSpinner />;
  }

  if (postError || commentsError) {
    return (
      <div className="p-6">
        <ErrorMessage error={postError || commentsError} onRetry={loadPostAndComments} onDismiss={() => {}} />
      </div>
    );
  }

  if (!fetchedPost?.data) {
    return <div className="text-center text-copy-light p-8">Blog post not found.</div>;
  }

  const post = fetchedPost.data;
  const comments = fetchedComments?.data || [];

  const renderComments = (commentsList: CommentResponse[]) => {
    return (
      <div className="space-y-4">
        {commentsList.map(comment => (
          <div key={comment.id} className="bg-surface p-4 rounded-lg shadow-sm">
            <div className="flex items-center mb-2">
              <div className="font-semibold text-main mr-2">{comment.author?.full_name || 'Anonymous'}</div>
              <div className="text-sm text-copy-light">{new Date(comment.created_at).toLocaleString()}</div>
            </div>
            <p className="text-copy">{comment.content}</p>
            {comment.replies && comment.replies.length > 0 && (
              <div className="ml-8 mt-4 border-l pl-4">
                {renderComments(comment.replies)}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <article className="prose lg:prose-xl mx-auto bg-surface p-8 rounded-lg shadow-md">
        <h1 className="text-main">{post.title}</h1>
        <div className="text-copy-light mb-4">
          By <span className="font-semibold">{post.author?.full_name || 'Anonymous'}</span> on {new Date(post.published_at || post.created_at).toLocaleDateString()}
          {post.category && (
            <span className="badge badge-outline ml-2">{post.category.name}</span>
          )}
          {post.tags && post.tags.map(tag => (
              <span key={tag.id} className="badge badge-secondary badge-outline ml-1">{tag.name}</span>
          ))}
        </div>
        {post.image_url && (
          <img src={post.image_url} alt={post.title} className="w-full rounded-lg mb-6" />
        )}
        <div dangerouslySetInnerHTML={{ __html: post.content }} className="text-copy" />
      </article>

      <section className="mx-auto mt-12 max-w-prose">
        <h2 className="text-3xl font-bold text-main mb-6">Comments</h2>
        {isAuthenticated ? (
          <form onSubmit={handleCommentSubmit} className="bg-surface p-6 rounded-lg shadow-sm mb-8">
            <h3 className="text-xl font-semibold text-main mb-4">Leave a Comment</h3>
            <Textarea
              label="Your Comment"
              value={commentContent}
              onChange={handleCommentChange}
              rows={4}
              required
            />
            <button type="submit" className="btn btn-primary mt-4" disabled={!commentContent.trim()}>
              Post Comment
            </button>
          </form>
        ) : (
          <p className="text-center text-copy-light mb-8">
            <Link to="/login" className="link link-primary">Log in</Link> to post a comment.
          </p>
        )}

        {comments.length === 0 ? (
          <div className="text-center text-copy-light">No comments yet. Be the first to comment!</div>
        ) : (
          renderComments(comments)
        )}
      </section>
    </div>
  );
};
