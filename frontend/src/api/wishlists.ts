import { apiClient } from './client';

interface WishlistCreateData {
  name: string;
  is_default?: boolean;
}

interface WishlistItemCreateData {
  product_id: string;
  variant_id?: string;
  quantity: number;
}

export class WishlistAPI {
  static async getWishlists(userId: string) {
    return await apiClient.get(`/users/${userId}/wishlists`);
  }

  static async createWishlist(userId: string, data: WishlistCreateData) {
    return await apiClient.post(`/users/${userId}/wishlists`, data);
  }

  static async addItemToWishlist(userId: string, wishlistId: string, data: WishlistItemCreateData) {
    return await apiClient.post(`/users/${userId}/wishlists/${wishlistId}/items`, data);
  }

  static async removeItemFromWishlist(userId: string, wishlistId: string, itemId: string) {
    return await apiClient.delete(`/users/${userId}/wishlists/${wishlistId}/items/${itemId}`);
  }

  static async clearWishlist(userId: string, wishlistId: string, itemIds: string[]) {
    // This is a custom implementation for clearing, as the backend doesn't have a direct clear endpoint
    // It will send multiple delete requests
    try {
      const deletePromises = itemIds.map(itemId =>
        apiClient.delete(`/users/${userId}/wishlists/${wishlistId}/items/${itemId}`)
      );
      await Promise.all(deletePromises);
      return { success: true, data: null, message: "Wishlist cleared successfully" };
    } catch (error) {
      console.error('Error clearing wishlist:', error);
      return { success: false, data: null, message: "Failed to clear wishlist" };
    }
  }

  static async setAsDefault(userId: string, wishlistId: string) {
    return await apiClient.put(`/users/${userId}/wishlists/${wishlistId}/default`);
  }
}

export default WishlistAPI;