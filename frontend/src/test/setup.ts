import { expect, afterEach, beforeAll, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { server } from './mocks/server';

// Setup MSW server
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

afterEach(() => {
  // Reset handlers after each test
  server.resetHandlers();
  // Cleanup React Testing Library
  cleanup();
  // Clear all mocks
  vi.clearAllMocks();
  // Clear localStorage and sessionStorage
  localStorage.clear();
  sessionStorage.clear();
});

afterAll(() => {
  server.close();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-object-url');
global.URL.revokeObjectURL = vi.fn();

// Mock FileReader
global.FileReader = class FileReader {
  result: string | null = null;
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  
  readAsDataURL(blob: Blob) {
    // Simulate async file reading
    setTimeout(() => {
      this.result = 'data:image/png;base64,mockbase64data';
      if (this.onload) {
        this.onload.call(this, {} as ProgressEvent<FileReader>);
      }
    }, 0);
  }
  
  addEventListener(event: string, handler: any) {
    if (event === 'load') {
      this.onload = handler;
    } else if (event === 'error') {
      this.onerror = handler;
    }
  }
  
  removeEventListener() {}
  abort() {}
  readAsText() {}
  readAsArrayBuffer() {}
  readAsBinaryString() {}
  
  EMPTY = 0;
  LOADING = 1;
  DONE = 2;
  readyState = 0;
  error: DOMException | null = null;
  
  dispatchEvent(event: Event): boolean {
    return true;
  }
} as any;
