import { apiClient } from './client';




class ReviewsAPI {
  async createReview(productId, rating, comment) {
    return apiClient.post('/reviews/', { product_id: productId, rating, comment });
  }

  async getProductReviews(productId, page = 1, limit = 10, minRating, maxRating, sortBy) {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    if (minRating !== undefined) {
      params.append('min_rating', minRating.toString());
    }
    if (maxRating !== undefined) {
      params.append('max_rating', maxRating.toString());
    }
    if (sortBy) {
      params.append('sort_by', sortBy);
    }
    return apiClient.get(`/reviews/product/${productId}?${params.toString()}`);
  }

  async getReview(reviewId) {
    return apiClient.get(`/reviews/${reviewId}`);
  }

  async updateReview(reviewId, rating, comment) {
    return apiClient.put(`/reviews/${reviewId}`, { rating, comment });
  }

  async deleteReview(reviewId) {
    return apiClient.delete(`/reviews/${reviewId}`);
  }
}

export default new ReviewsAPI();