/**
 * Brands API endpoints (placeholder for future implementation)
 */

import { apiClient   } from './client';



export class BrandsAPI {
    /**
     * Get all brands (placeholder)
     */
    static async getBrands() {
        return await apiClient.get('/brands');
    }

    /**
     * Get brand by ID (placeholder)
     */
    static async getBrand(id: string) {
        return await apiClient.get(`/brands/${id}`);
    }
}

export default BrandsAPI;