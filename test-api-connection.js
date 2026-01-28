#!/usr/bin/env node

/**
 * Simple script to test API connection between frontend and backend
 */

const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000/v1';

async function testConnection() {
  console.log('🔍 Testing API connection...\n');

  const tests = [
    {
      name: 'Health Check',
      method: 'GET',
      url: `${API_BASE_URL}/../health`,
      expectedStatus: 200
    },
    {
      name: 'Products List',
      method: 'GET',
      url: `${API_BASE_URL}/products`,
      expectedStatus: 200
    },
    {
      name: 'Product Categories',
      method: 'GET',
      url: `${API_BASE_URL}/products/categories`,
      expectedStatus: 200
    },
    {
      name: 'Cart (Guest)',
      method: 'GET',
      url: `${API_BASE_URL}/cart`,
      expectedStatus: [200, 401] // 401 is acceptable for guest users
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      console.log(`Testing: ${test.name}`);
      const response = await axios({
        method: test.method,
        url: test.url,
        timeout: 5000,
        validateStatus: () => true // Don't throw on any status
      });

      const expectedStatuses = Array.isArray(test.expectedStatus) 
        ? test.expectedStatus 
        : [test.expectedStatus];

      if (expectedStatuses.includes(response.status)) {
        console.log(`✅ ${test.name}: ${response.status} - OK`);
        passed++;
      } else {
        console.log(`❌ ${test.name}: ${response.status} - Expected ${test.expectedStatus}`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${test.name}: ${error.message}`);
      failed++;
    }
    console.log('');
  }

  console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);
  
  if (failed === 0) {
    console.log('🎉 All API connections working!');
    process.exit(0);
  } else {
    console.log('⚠️  Some API connections failed. Check if backend is running on http://localhost:8000');
    process.exit(1);
  }
}

// Run the test
testConnection().catch(error => {
  console.error('❌ Test failed:', error.message);
  process.exit(1);
});