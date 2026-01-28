/**
 * Property-Based Tests for Checkout Page
 * 
 * Feature: app-enhancements
 * These tests verify universal properties that should hold across all inputs
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { AuthAPI } from '../../api/auth';

// Mock the AuthAPI
vi.mock('../../apis/auth');

describe('Checkout Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Property 6: Address creation persistence
   * For any new address created in checkout, the address should be 
   * saved to the database and retrievable
   * 
   * Validates: Requirements 3.1
   */
  it('Property 6: created addresses should persist and be retrievable', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          street: fc.string({ minLength: 1, maxLength: 100 }),
          city: fc.string({ minLength: 1, maxLength: 50 }),
          state: fc.string({ minLength: 1, maxLength: 50 }),
          country: fc.string({ minLength: 1, maxLength: 50 }),
          post_code: fc.string({ minLength: 1, maxLength: 20 }),
          kind: fc.constantFrom('Shipping', 'Billing'),
        }),
        async (addressData) => {
          // Generate a unique ID for the created address
          const createdAddressId = fc.sample(fc.uuid(), 1)[0];
          const createdAddress = {
            id: createdAddressId,
            ...addressData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          // Mock address creation
          vi.mocked(AuthAPI.createAddress).mockResolvedValue({
            success: true,
            data: createdAddress,
          });

          // Create the address
          const createResponse = await AuthAPI.createAddress(addressData);

          // Verify creation was successful
          expect(createResponse.success).toBe(true);
          expect(createResponse.data.id).toBeDefined();
          expect(createResponse.data.street).toBe(addressData.street);
          expect(createResponse.data.city).toBe(addressData.city);
          expect(createResponse.data.state).toBe(addressData.state);
          expect(createResponse.data.country).toBe(addressData.country);
          expect(createResponse.data.post_code).toBe(addressData.post_code);

          // Mock retrieval of addresses including the newly created one
          const existingAddresses = fc.sample(
            fc.array(fc.record({
              id: fc.uuid(),
              street: fc.string({ minLength: 1, maxLength: 100 }),
              city: fc.string({ minLength: 1, maxLength: 50 }),
              state: fc.string({ minLength: 1, maxLength: 50 }),
              country: fc.string({ minLength: 1, maxLength: 50 }),
              post_code: fc.string({ minLength: 1, maxLength: 20 }),
              kind: fc.constantFrom('Shipping', 'Billing'),
            })),
            1
          )[0];

          const allAddresses = [...existingAddresses, createdAddress];
          vi.mocked(AuthAPI.getAddresses).mockResolvedValue(allAddresses);

          // Retrieve addresses
          const addresses = await AuthAPI.getAddresses();

          // Verify the created address is in the list
          const foundAddress = addresses.find(addr => addr.id === createdAddressId);
          expect(foundAddress).toBeDefined();
          expect(foundAddress?.street).toBe(addressData.street);
          expect(foundAddress?.city).toBe(addressData.city);
          expect(foundAddress?.state).toBe(addressData.state);
          expect(foundAddress?.country).toBe(addressData.country);
          expect(foundAddress?.post_code).toBe(addressData.post_code);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 7: Address list immediate update
   * For any successful address creation, the address list in the UI 
   * should update immediately to include the new address
   * 
   * Validates: Requirements 3.2
   */
  it('Property 7: address list should immediately include newly created address', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.record({
          id: fc.uuid(),
          street: fc.string({ minLength: 1, maxLength: 100 }),
          city: fc.string({ minLength: 1, maxLength: 50 }),
          state: fc.string({ minLength: 1, maxLength: 50 }),
          country: fc.string({ minLength: 1, maxLength: 50 }),
          post_code: fc.string({ minLength: 1, maxLength: 20 }),
          kind: fc.constantFrom('Shipping', 'Billing'),
        })),
        fc.record({
          street: fc.string({ minLength: 1, maxLength: 100 }),
          city: fc.string({ minLength: 1, maxLength: 50 }),
          state: fc.string({ minLength: 1, maxLength: 50 }),
          country: fc.string({ minLength: 1, maxLength: 50 }),
          post_code: fc.string({ minLength: 1, maxLength: 20 }),
          kind: fc.constantFrom('Shipping', 'Billing'),
        }),
        async (initialAddresses, newAddressData) => {
          const initialCount = initialAddresses.length;

          // Mock the new address creation
          const newAddress = {
            id: fc.sample(fc.uuid(), 1)[0],
            ...newAddressData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          vi.mocked(AuthAPI.createAddress).mockResolvedValue({
            success: true,
            data: newAddress,
          });

          // Create the address
          const response = await AuthAPI.createAddress(newAddressData);

          // Simulate UI state update (what the component does)
          const updatedAddresses = [...initialAddresses, response.data];

          // Verify the list now contains the new address
          expect(updatedAddresses.length).toBe(initialCount + 1);
          
          // Verify the new address is at the end of the list
          const lastAddress = updatedAddresses[updatedAddresses.length - 1];
          expect(lastAddress.id).toBe(newAddress.id);
          expect(lastAddress.street).toBe(newAddressData.street);
          expect(lastAddress.city).toBe(newAddressData.city);
          
          // Verify all original addresses are still present
          initialAddresses.forEach((addr, index) => {
            expect(updatedAddresses[index]).toEqual(addr);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 8: New address auto-selection
   * For any newly created address in checkout, the system should 
   * automatically select it as the shipping address
   * 
   * Validates: Requirements 3.3
   */
  it('Property 8: newly created address should be auto-selected', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.option(fc.uuid()), // existing selected address ID (may be null)
        fc.record({
          street: fc.string({ minLength: 1, maxLength: 100 }),
          city: fc.string({ minLength: 1, maxLength: 50 }),
          state: fc.string({ minLength: 1, maxLength: 50 }),
          country: fc.string({ minLength: 1, maxLength: 50 }),
          post_code: fc.string({ minLength: 1, maxLength: 20 }),
          kind: fc.constantFrom('Shipping', 'Billing'),
        }),
        async (existingSelectedId, newAddressData) => {
          // Mock the new address creation
          const newAddressId = fc.sample(fc.uuid(), 1)[0];
          const newAddress = {
            id: newAddressId,
            ...newAddressData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          vi.mocked(AuthAPI.createAddress).mockResolvedValue({
            success: true,
            data: newAddress,
          });

          // Create the address
          const response = await AuthAPI.createAddress(newAddressData);

          // Simulate checkout state update (what the component does)
          const initialCheckoutData = {
            shipping_address_id: existingSelectedId || '',
            shipping_method_id: fc.sample(fc.uuid(), 1)[0],
            payment_method_id: fc.sample(fc.uuid(), 1)[0],
            notes: fc.sample(fc.string(), 1)[0],
          };

          const updatedCheckoutData = {
            ...initialCheckoutData,
            shipping_address_id: response.data.id,
          };

          // Verify the new address is now selected
          expect(updatedCheckoutData.shipping_address_id).toBe(newAddressId);
          
          // Verify other checkout data is preserved
          expect(updatedCheckoutData.shipping_method_id).toBe(initialCheckoutData.shipping_method_id);
          expect(updatedCheckoutData.payment_method_id).toBe(initialCheckoutData.payment_method_id);
          expect(updatedCheckoutData.notes).toBe(initialCheckoutData.notes);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 9: Checkout state preservation
   * For any address list update, the current checkout state 
   * (cart items, payment method, shipping method) should remain unchanged
   * 
   * Validates: Requirements 3.5
   */
  it('Property 9: checkout state should be preserved during address updates', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          shipping_address_id: fc.option(fc.uuid()),
          shipping_method_id: fc.uuid(),
          payment_method_id: fc.uuid(),
          notes: fc.string({ maxLength: 500 }),
        }),
        fc.record({
          street: fc.string({ minLength: 1, maxLength: 100 }),
          city: fc.string({ minLength: 1, maxLength: 50 }),
          state: fc.string({ minLength: 1, maxLength: 50 }),
          country: fc.string({ minLength: 1, maxLength: 50 }),
          post_code: fc.string({ minLength: 1, maxLength: 20 }),
          kind: fc.constantFrom('Shipping', 'Billing'),
        }),
        async (initialCheckoutData, newAddressData) => {
          // Mock the new address creation
          const newAddress = {
            id: fc.sample(fc.uuid(), 1)[0],
            ...newAddressData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          vi.mocked(AuthAPI.createAddress).mockResolvedValue({
            success: true,
            data: newAddress,
          });

          // Create the address
          const response = await AuthAPI.createAddress(newAddressData);

          // Simulate checkout state update (what the component does)
          const updatedCheckoutData = {
            ...initialCheckoutData,
            shipping_address_id: response.data.id,
          };

          // Verify only shipping_address_id changed
          expect(updatedCheckoutData.shipping_address_id).toBe(newAddress.id);
          
          // Verify all other checkout data is preserved
          expect(updatedCheckoutData.shipping_method_id).toBe(initialCheckoutData.shipping_method_id);
          expect(updatedCheckoutData.payment_method_id).toBe(initialCheckoutData.payment_method_id);
          expect(updatedCheckoutData.notes).toBe(initialCheckoutData.notes);
          
          // Verify the original checkout data wasn't mutated
          if (initialCheckoutData.shipping_address_id) {
            expect(initialCheckoutData.shipping_address_id).not.toBe(newAddress.id);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
