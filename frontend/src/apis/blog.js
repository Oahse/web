import { apiClient } from './client';


class BlogAPI {
  
  async createBlogPost(data) {
    return apiClient.post('/blog/', data);
  }

   
  async getBlogPosts(page = 1, limit = 10, is_published, search) {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    if (is_published !== undefined) {
      params.append('is_published', is_published.toString());
    }
    if (search) {
      params.append('search', search);
    }
    return apiClient.get(`/blog/?${params.toString()}`);
  }

   
  async getBlogPost(postId) {
    return apiClient.get(`/blog/${postId}`);
  }

   
  async updateBlogPost(postId, data) {
    return apiClient.put(`/blog/${postId}`, data);
  }

   
  async deleteBlogPost(postId) {
    return apiClient.delete(`/blog/${postId}`);
  }
}

export default new BlogAPI();