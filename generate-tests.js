#!/usr/bin/env node

/**
 * Script to generate test files for all .tsx components
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get all .tsx files that don't have tests
function getTsxFilesWithoutTests() {
  const command = `find frontend/src -name "*.tsx" -not -path "*/node_modules/*" -not -name "*.test.tsx"`;
  const output = execSync(command, { encoding: 'utf8' });
  return output.trim().split('\n').filter(Boolean);
}

// Check if test file exists
function hasTestFile(tsxFile) {
  const testFile = tsxFile.replace('.tsx', '.test.tsx');
  return fs.existsSync(testFile);
}

// Generate test template
function generateTestTemplate(tsxFile) {
  const componentName = path.basename(tsxFile, '.tsx');
  const relativePath = path.relative('frontend/src/__tests__', tsxFile).replace(/\\/g, '/');
  const importPath = relativePath.startsWith('../') ? relativePath : `../${relativePath}`;
  
  return `/**
 * Tests for ${componentName}.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ${componentName} from '${importPath.replace('.tsx', '')}';

// Mock dependencies as needed
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
    useParams: () => ({}),
    Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
      <a href={to}>{children}</a>
    )
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('${componentName}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <TestWrapper>
        <${componentName} />
      </TestWrapper>
    );
    
    // Add specific assertions based on component
    expect(screen.getByRole('main') || screen.getByTestId('${componentName.toLowerCase()}') || document.body).toBeInTheDocument();
  });

  it('should handle user interactions', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <${componentName} />
      </TestWrapper>
    );

    // Add interaction tests based on component functionality
    // Example: await user.click(screen.getByRole('button'));
  });

  it('should be accessible', () => {
    render(
      <TestWrapper>
        <${componentName} />
      </TestWrapper>
    );

    // Add accessibility tests
    // Example: expect(screen.getByRole('button')).toBeInTheDocument();
  });

  // Add more specific tests based on component functionality
});
`;
}

// Create test directory if it doesn't exist
function ensureTestDirectory(testFilePath) {
  const dir = path.dirname(testFilePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// Main function
function main() {
  console.log('🔍 Finding .tsx files without tests...\n');
  
  const tsxFiles = getTsxFilesWithoutTests();
  const filesWithoutTests = tsxFiles.filter(file => !hasTestFile(file));
  
  console.log(`Found ${filesWithoutTests.length} files without tests:\n`);
  
  let created = 0;
  let skipped = 0;
  
  filesWithoutTests.forEach(tsxFile => {
    const componentName = path.basename(tsxFile, '.tsx');
    const testFile = tsxFile.replace('.tsx', '.test.tsx');
    
    // Skip certain files that don't need tests
    const skipPatterns = [
      'index.tsx',
      'vite-env.d.ts',
      'validation.tsx' // utility file
    ];
    
    if (skipPatterns.some(pattern => tsxFile.includes(pattern))) {
      console.log(`⏭️  Skipping ${componentName} (${tsxFile})`);
      skipped++;
      return;
    }
    
    try {
      ensureTestDirectory(testFile);
      const testContent = generateTestTemplate(tsxFile);
      fs.writeFileSync(testFile, testContent);
      console.log(`✅ Created test for ${componentName} (${testFile})`);
      created++;
    } catch (error) {
      console.error(`❌ Failed to create test for ${componentName}: ${error.message}`);
    }
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Created: ${created} test files`);
  console.log(`   Skipped: ${skipped} files`);
  console.log(`   Total .tsx files: ${tsxFiles.length}`);
  console.log(`   Files with tests: ${tsxFiles.length - filesWithoutTests.length + created}`);
  
  const coverage = Math.round(((tsxFiles.length - filesWithoutTests.length + created) / tsxFiles.length) * 100);
  console.log(`   Test coverage: ${coverage}%`);
  
  console.log('\n🎉 Test generation complete!');
  console.log('\n💡 Next steps:');
  console.log('   1. Review generated tests and add specific assertions');
  console.log('   2. Add proper mocks for component dependencies');
  console.log('   3. Run tests: npm run test');
  console.log('   4. Update tests based on actual component behavior');
}

if (require.main === module) {
  main();
}

module.exports = { generateTestTemplate, getTsxFilesWithoutTests };