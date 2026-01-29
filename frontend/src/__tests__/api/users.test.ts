/**
 * Tests for Users API - Comprehensive test suite aligned with backend reality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UsersAPI } from '../../api/users';
import { apiClient } from '../../api/client';

// Mock the API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn()
  }
}));

const mockApiClient = vi.mocked(apiClient);

describe('UsersAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getProfile', () => {
    it('should get user profile with correct backend format', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 'user123',
          email: 'john.doe@example.com',
          firstname: 'John',
          lastname: 'Doe',
          full_name: 'John Doe',
          phone: '+1234567890',
          role: 'Customer',
          verified: true,
          is_active: true,
          age: 30,
          gender: 'male',
          country: 'US',
          language: 'en',
          timezone: 'America/New_York',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-15T10:00:00Z'
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getProfile();

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users/profile');
      expect(result).toEqual(mockResponse);
    });

    it('should handle unauthorized access to profile', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            message: 'Authentication required'
          }
        }
      };

      mockApiClient.get.mockRejectedValue(mockError);

      await expect(UsersAPI.getProfile()).rejects.toEqual(mockError);
    });

    it('should handle profile not found', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            message: 'User profile not found'
          }
        }
      };

      mockApiClient.get.mockRejectedValue(mockError);

      await expect(UsersAPI.getProfile()).rejects.toEqual(mockError);
    });
  });

  describe('updateProfile', () => {
    it('should update user profile with valid data', async () => {
      const profileData = {
        firstname: 'Jane',
        lastname: 'Smith',
        phone: '+1987654321',
        age: 28,
        gender: 'female',
        country: 'CA',
        language: 'en',
        timezone: 'America/Toronto'
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'user123',
          email: 'jane.smith@example.com',
          firstname: 'Jane',
          lastname: 'Smith',
          full_name: 'Jane Smith',
          phone: '+1987654321',
          role: 'Customer',
          verified: true,
          is_active: true,
          age: 28,
          gender: 'female',
          country: 'CA',
          language: 'en',
          timezone: 'America/Toronto',
          updated_at: '2024-01-15T10:00:00Z'
        },
        message: 'Profile updated successfully'
      };

      mockApiClient.put.mockResolvedValue(mockResponse);

      const result = await UsersAPI.updateProfile(profileData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/v1/users/profile', profileData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle partial profile updates', async () => {
      const partialData = {
        phone: '+1555123456'
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'user123',
          email: 'john.doe@example.com',
          firstname: 'John',
          lastname: 'Doe',
          phone: '+1555123456', // Updated field
          updated_at: '2024-01-15T10:00:00Z'
        },
        message: 'Profile updated successfully'
      };

      mockApiClient.put.mockResolvedValue(mockResponse);

      const result = await UsersAPI.updateProfile(partialData);

      expect(result.data.phone).toBe('+1555123456');
    });

    it('should handle validation errors during profile update', async () => {
      const invalidData = {
        email: 'invalid-email',
        phone: '123', // Too short
        age: -5 // Invalid age
      };

      const mockError = {
        response: {
          status: 422,
          data: {
            message: 'Validation error',
            details: {
              email: ['Invalid email format'],
              phone: ['Phone number must be at least 10 digits'],
              age: ['Age must be positive']
            }
          }
        }
      };

      mockApiClient.put.mockRejectedValue(mockError);

      await expect(UsersAPI.updateProfile(invalidData)).rejects.toEqual(mockError);
    });

    it('should handle unauthorized profile update', async () => {
      const profileData = { firstname: 'Unauthorized' };
      const mockError = {
        response: {
          status: 401,
          data: {
            message: 'Authentication required'
          }
        }
      };

      mockApiClient.put.mockRejectedValue(mockError);

      await expect(UsersAPI.updateProfile(profileData)).rejects.toEqual(mockError);
    });
  });

  describe('searchUsers', () => {
    it('should search users with advanced fuzzy matching', async () => {
      const query = 'john';
      const filters = {
        role: 'Customer',
        limit: 20
      };

      const mockResponse = {
        success: true,
        data: {
          query: query,
          filters: filters,
          users: [
            {
              id: 'user123',
              email: 'john.doe@example.com',
              firstname: 'John',
              lastname: 'Doe',
              role: 'Customer',
              relevance_score: 0.95
            },
            {
              id: 'user456',
              email: 'johnny.smith@example.com',
              firstname: 'Johnny',
              lastname: 'Smith',
              role: 'Customer',
              relevance_score: 0.85
            }
          ],
          count: 2
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.searchUsers(query, filters);

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users/search?q=john&role=Customer&limit=20');
      expect(result).toEqual(mockResponse);
    });

    it('should search users without filters', async () => {
      const query = 'jane';
      const mockResponse = {
        success: true,
        data: {
          query: query,
          users: [
            {
              id: 'user789',
              email: 'jane.doe@example.com',
              firstname: 'Jane',
              lastname: 'Doe',
              role: 'Customer'
            }
          ],
          count: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.searchUsers(query, {});

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users/search?q=jane');
      expect(result).toEqual(mockResponse);
    });

    it('should handle empty search results', async () => {
      const query = 'nonexistentuser';
      const mockResponse = {
        success: true,
        data: {
          query: query,
          users: [],
          count: 0
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.searchUsers(query, {});

      expect(result.data.users).toHaveLength(0);
      expect(result.data.count).toBe(0);
    });

    it('should handle admin-only search access', async () => {
      const query = 'admin';
      const mockError = {
        response: {
          status: 403,
          data: {
            message: 'Admin access required for user search'
          }
        }
      };

      mockApiClient.get.mockRejectedValue(mockError);

      await expect(UsersAPI.searchUsers(query, {})).rejects.toEqual(mockError);
    });
  });

  describe('getUsers', () => {
    it('should get users list with pagination and filters', async () => {
      const params = {
        page: 1,
        limit: 25,
        role: 'Supplier',
        q: 'tech',
        search_mode: 'advanced'
      };

      const mockResponse = {
        success: true,
        data: {
          data: [
            {
              id: 'user123',
              email: 'tech.supplier@example.com',
              firstname: 'Tech',
              lastname: 'Supplier',
              role: 'Supplier',
              verified: true,
              is_active: true,
              created_at: '2024-01-01T00:00:00Z'
            }
          ],
          total: 1,
          page: 1,
          per_page: 25,
          total_pages: 1,
          search_mode: 'advanced'
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getUsers(params);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/v1/users?page=1&limit=25&role=Supplier&q=tech&search_mode=advanced'
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get users without filters', async () => {
      const mockResponse = {
        success: true,
        data: {
          data: [
            {
              id: 'user123',
              email: 'user1@example.com',
              firstname: 'User',
              lastname: 'One',
              role: 'Customer'
            },
            {
              id: 'user456',
              email: 'user2@example.com',
              firstname: 'User',
              lastname: 'Two',
              role: 'Customer'
            }
          ],
          total: 2,
          page: 1,
          per_page: 10,
          total_pages: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getUsers({});

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users');
      expect(result).toEqual(mockResponse);
    });

    it('should handle role-based filtering', async () => {
      const params = {
        role: 'Admin',
        page: 1,
        limit: 10
      };

      const mockResponse = {
        success: true,
        data: {
          data: [
            {
              id: 'admin123',
              email: 'admin@example.com',
              firstname: 'Admin',
              lastname: 'User',
              role: 'Admin',
              verified: true,
              is_active: true
            }
          ],
          total: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getUsers(params);

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users?page=1&limit=10&role=Admin');
      expect(result.data.data[0].role).toBe('Admin');
    });

    it('should handle advanced search mode', async () => {
      const params = {
        q: 'supplier tech',
        search_mode: 'advanced',
        limit: 15
      };

      const mockResponse = {
        success: true,
        data: {
          data: [
            {
              id: 'user123',
              email: 'tech.supplier@example.com',
              firstname: 'Tech',
              lastname: 'Supplier',
              role: 'Supplier',
              relevance_score: 0.92
            }
          ],
          total: 1,
          search_mode: 'advanced'
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getUsers(params);

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/users?limit=15&q=supplier+tech&search_mode=advanced');
      expect(result.data.search_mode).toBe('advanced');
    });

    it('should handle pagination correctly', async () => {
      const params = {
        page: 3,
        limit: 50
      };

      const mockResponse = {
        success: true,
        data: {
          data: [],
          total: 125,
          page: 3,
          per_page: 50,
          total_pages: 3
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getUsers(params);

      expect(result.data.page).toBe(3);
      expect(result.data.total_pages).toBe(3);
      expect(result.data.per_page).toBe(50);
    });

    it('should handle admin access required error', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            message: 'Admin access required to list users'
          }
        }
      };

      mockApiClient.get.mockRejectedValue(mockError);

      await expect(UsersAPI.getUsers({})).rejects.toEqual(mockError);
    });
  });

  describe('Error Handling', () => {
    it('should handle network timeouts', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      };

      mockApiClient.get.mockRejectedValue(timeoutError);

      await expect(UsersAPI.getProfile()).rejects.toEqual(timeoutError);
    });

    it('should handle server errors consistently', async () => {
      const serverError = {
        response: {
          status: 500,
          data: {
            message: 'Internal server error'
          }
        }
      };

      mockApiClient.put.mockRejectedValue(serverError);

      await expect(UsersAPI.updateProfile({})).rejects.toEqual(serverError);
    });

    it('should handle rate limiting', async () => {
      const rateLimitError = {
        response: {
          status: 429,
          data: {
            message: 'Too many requests. Please try again later.',
            retry_after: 60
          }
        }
      };

      mockApiClient.get.mockRejectedValue(rateLimitError);

      await expect(UsersAPI.searchUsers('test', {})).rejects.toEqual(rateLimitError);
    });
  });

  describe('Data Validation', () => {
    it('should handle profile data with all supported fields', async () => {
      const completeProfileData = {
        firstname: 'Complete',
        lastname: 'User',
        phone: '+1234567890',
        age: 25,
        gender: 'non-binary',
        country: 'GB',
        language: 'en-GB',
        timezone: 'Europe/London',
        bio: 'Complete user profile',
        preferences: {
          newsletter: true,
          marketing_emails: false,
          sms_notifications: true
        }
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'user123',
          ...completeProfileData,
          full_name: 'Complete User',
          updated_at: '2024-01-15T10:00:00Z'
        }
      };

      mockApiClient.put.mockResolvedValue(mockResponse);

      const result = await UsersAPI.updateProfile(completeProfileData);

      expect(result.data.firstname).toBe('Complete');
      expect(result.data.lastname).toBe('User');
      expect(result.data.country).toBe('GB');
      expect(result.data.preferences).toEqual(completeProfileData.preferences);
    });

    it('should handle search with multiple role filters', async () => {
      const query = 'user';
      const filters = {
        role: 'Customer,Supplier', // Multiple roles
        limit: 30
      };

      const mockResponse = {
        success: true,
        data: {
          users: [
            { id: 'user1', role: 'Customer', firstname: 'Customer', lastname: 'User' },
            { id: 'user2', role: 'Supplier', firstname: 'Supplier', lastname: 'User' }
          ],
          count: 2
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.searchUsers(query, filters);

      expect(result.data.users).toHaveLength(2);
      expect(result.data.users[0].role).toBe('Customer');
      expect(result.data.users[1].role).toBe('Supplier');
    });
  });

  describe('Integration Scenarios', () => {
    it('should handle user profile with address information', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 'user123',
          email: 'user@example.com',
          firstname: 'John',
          lastname: 'Doe',
          addresses: [
            {
              id: 'addr123',
              type: 'shipping',
              street: '123 Main St',
              city: 'New York',
              state: 'NY',
              postal_code: '10001',
              country: 'US',
              is_default: true
            }
          ],
          payment_methods: [
            {
              id: 'pm123',
              type: 'card',
              last4: '4242',
              is_default: true
            }
          ]
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.getProfile();

      expect(result.data.addresses).toHaveLength(1);
      expect(result.data.payment_methods).toHaveLength(1);
      expect(result.data.addresses[0].is_default).toBe(true);
    });

    it('should handle user search with location-based filtering', async () => {
      const query = 'supplier';
      const filters = {
        country: 'US',
        state: 'CA',
        role: 'Supplier'
      };

      const mockResponse = {
        success: true,
        data: {
          users: [
            {
              id: 'supplier123',
              firstname: 'California',
              lastname: 'Supplier',
              role: 'Supplier',
              country: 'US',
              state: 'CA'
            }
          ],
          count: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await UsersAPI.searchUsers(query, filters);

      expect(result.data.users[0].country).toBe('US');
      expect(result.data.users[0].state).toBe('CA');
    });
  });
});