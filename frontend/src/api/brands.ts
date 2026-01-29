/**
 * Brands API endpoints (placeholder for future implementation)
 * 
 * ACCESS LEVELS:
 * - Public: View brands and brand details
 * - Admin: Create, update, delete brands (future implementation)
 */

import { apiClient   } from './client';



export class BrandsAPI {
    /**
     * Get all brands (placeholder)
     * ACCESS: Public - No authentication required
     */
    static async getBrands() {
        return await apiClient.get('/brands');
    }

    /**
     * Get brand by ID (placeholder)
     * ACCESS: Public - No authentication required
     */
    static async getBrand(id: string) {
        return await apiClient.get(`/brands/${id}`);
    }
}

export default BrandsAPI;