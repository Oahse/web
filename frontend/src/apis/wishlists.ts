import { apiClient } from './client';


export class WishlistAPI {
  static async getWishlists(userId) {
    return await apiClient.get(`/users/${userId}/wishlists`);
  }

  static async createWishlist(userId, data) {
    return await apiClient.post(`/users/${userId}/wishlists`, data);
  }

  static async addItemToWishlist(userId, wishlistId, data) {
    return await apiClient.post(`/users/${userId}/wishlists/${wishlistId}/items`, data);
  }

  static async removeItemFromWishlist(userId, wishlistId, itemId) {
    return await apiClient.delete(`/users/${userId}/wishlists/${wishlistId}/items/${itemId}`);
  }

  static async clearWishlist(userId, wishlistId, itemIds) {
    // This is a custom implementation for clearing, as the backend doesn't have a direct clear endpoint
    // It will send multiple delete requests
    const deletePromises = itemIds.map(itemId =>
      apiClient.delete(`/users/${userId}/wishlists/${wishlistId}/items/${itemId}`)
    );
    await Promise.all(deletePromises);
    return { success: true, data: null, message: "Wishlist cleared successfully" };
  }

  static async setAsDefault(userId, wishlistId) {
    // Assuming a PUT endpoint for setting default wishlist
    return await apiClient.put(`/users/${userId}/wishlists/${wishlistId}/default`);
  }
}

export default WishlistAPI;