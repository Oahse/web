/**
 * Cart Test Runner
 * Runs all cart-related tests and generates a comprehensive report
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { join } from 'path';

interface TestResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  errors?: string[];
}

interface TestSuite {
  name: string;
  tests: TestResult[];
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  duration: number;
}

class CartTestRunner {
  private results: TestSuite[] = [];

  async runAllCartTests(): Promise<void> {
    console.log('🛒 Starting Cart Test Suite...\n');

    const testSuites = [
      {
        name: 'Cart Context Tests',
        pattern: 'src/contexts/__tests__/CartContext.test.tsx',
        description: 'Tests cart context state management and API integration'
      },
      {
        name: 'Cart Page Comprehensive Tests',
        pattern: 'src/test/integration/cart-page-comprehensive.test.tsx',
        description: 'Tests complete cart page functionality including UI and interactions'
      },
      {
        name: 'Product Card Cart Integration',
        pattern: 'src/test/integration/product-card-cart-integration.test.tsx',
        description: 'Tests add to cart functionality from product cards'
      },
      {
        name: 'Cart Real-time Updates',
        pattern: 'src/test/integration/cart-realtime-updates.test.tsx',
        description: 'Tests real-time cart synchronization and updates'
      }
    ];

    for (const suite of testSuites) {
      await this.runTestSuite(suite);
    }

    this.generateReport();
  }

  private async runTestSuite(suite: { name: string; pattern: string; description: string }): Promise<void> {
    console.log(`📋 Running: ${suite.name}`);
    console.log(`   ${suite.description}\n`);

    const startTime = Date.now();
    
    try {
      const command = `npm run test -- ${suite.pattern} --reporter=json`;
      const output = execSync(command, { 
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: 60000 // 1 minute timeout
      });

      const result = this.parseTestOutput(output);
      const duration = Date.now() - startTime;

      this.results.push({
        name: suite.name,
        tests: result.tests,
        totalTests: result.totalTests,
        passedTests: result.passedTests,
        failedTests: result.failedTests,
        skippedTests: result.skippedTests,
        duration
      });

      console.log(`   ✅ ${result.passedTests}/${result.totalTests} tests passed (${duration}ms)\n`);

    } catch (error: any) {
      console.log(`   ❌ Test suite failed: ${error.message}\n`);
      
      this.results.push({
        name: suite.name,
        tests: [],
        totalTests: 0,
        passedTests: 0,
        failedTests: 1,
        skippedTests: 0,
        duration: Date.now() - startTime
      });
    }
  }

  private parseTestOutput(output: string): {
    tests: TestResult[];
    totalTests: number;
    passedTests: number;
    failedTests: number;
    skippedTests: number;
  } {
    // This is a simplified parser - in reality you'd parse the JSON output from vitest
    const lines = output.split('\n');
    const tests: TestResult[] = [];
    let totalTests = 0;
    let passedTests = 0;
    let failedTests = 0;
    let skippedTests = 0;

    // Parse test results (simplified)
    for (const line of lines) {
      if (line.includes('✓') || line.includes('PASS')) {
        passedTests++;
        totalTests++;
      } else if (line.includes('✗') || line.includes('FAIL')) {
        failedTests++;
        totalTests++;
      } else if (line.includes('○') || line.includes('SKIP')) {
        skippedTests++;
        totalTests++;
      }
    }

    return {
      tests,
      totalTests,
      passedTests,
      failedTests,
      skippedTests
    };
  }

  private generateReport(): void {
    const totalTests = this.results.reduce((sum, suite) => sum + suite.totalTests, 0);
    const totalPassed = this.results.reduce((sum, suite) => sum + suite.passedTests, 0);
    const totalFailed = this.results.reduce((sum, suite) => sum + suite.failedTests, 0);
    const totalSkipped = this.results.reduce((sum, suite) => sum + suite.skippedTests, 0);
    const totalDuration = this.results.reduce((sum, suite) => sum + suite.duration, 0);

    console.log('\n' + '='.repeat(80));
    console.log('🛒 CART TEST SUITE RESULTS');
    console.log('='.repeat(80));
    
    console.log(`\n📊 Overall Summary:`);
    console.log(`   Total Tests: ${totalTests}`);
    console.log(`   Passed: ${totalPassed} (${((totalPassed / totalTests) * 100).toFixed(1)}%)`);
    console.log(`   Failed: ${totalFailed} (${((totalFailed / totalTests) * 100).toFixed(1)}%)`);
    console.log(`   Skipped: ${totalSkipped} (${((totalSkipped / totalTests) * 100).toFixed(1)}%)`);
    console.log(`   Duration: ${totalDuration}ms`);

    console.log(`\n📋 Test Suite Breakdown:`);
    for (const suite of this.results) {
      const passRate = suite.totalTests > 0 ? ((suite.passedTests / suite.totalTests) * 100).toFixed(1) : '0.0';
      const status = suite.failedTests === 0 ? '✅' : '❌';
      
      console.log(`   ${status} ${suite.name}`);
      console.log(`      ${suite.passedTests}/${suite.totalTests} passed (${passRate}%) - ${suite.duration}ms`);
    }

    // Generate detailed HTML report
    this.generateHTMLReport();

    console.log(`\n📄 Detailed report generated: cart-test-report.html`);
    
    if (totalFailed > 0) {
      console.log(`\n❌ ${totalFailed} test(s) failed. Please review and fix the issues.`);
      process.exit(1);
    } else {
      console.log(`\n🎉 All cart tests passed! Your cart functionality is working correctly.`);
    }
  }

  private generateHTMLReport(): void {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cart Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .metric {
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .total { color: #007bff; }
        .suites {
            padding: 30px;
        }
        .suite {
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        .suite-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        .suite-title {
            margin: 0;
            font-size: 1.3em;
            color: #333;
        }
        .suite-stats {
            margin-top: 10px;
            display: flex;
            gap: 20px;
            font-size: 0.9em;
        }
        .suite-body {
            padding: 20px;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: #28a745;
            transition: width 0.3s ease;
        }
        .timestamp {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 Cart Test Report</h1>
            <p>Comprehensive testing results for cart functionality</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value total">${this.results.reduce((sum, suite) => sum + suite.totalTests, 0)}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value passed">${this.results.reduce((sum, suite) => sum + suite.passedTests, 0)}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value failed">${this.results.reduce((sum, suite) => sum + suite.failedTests, 0)}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value skipped">${this.results.reduce((sum, suite) => sum + suite.skippedTests, 0)}</div>
                <div class="metric-label">Skipped</div>
            </div>
        </div>
        
        <div class="suites">
            <h2>Test Suites</h2>
            ${this.results.map(suite => {
              const passRate = suite.totalTests > 0 ? (suite.passedTests / suite.totalTests) * 100 : 0;
              return `
                <div class="suite">
                    <div class="suite-header">
                        <h3 class="suite-title">${suite.failedTests === 0 ? '✅' : '❌'} ${suite.name}</h3>
                        <div class="suite-stats">
                            <span class="passed">${suite.passedTests} passed</span>
                            <span class="failed">${suite.failedTests} failed</span>
                            <span class="skipped">${suite.skippedTests} skipped</span>
                            <span>${suite.duration}ms</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${passRate}%"></div>
                        </div>
                    </div>
                    <div class="suite-body">
                        <p><strong>Coverage:</strong> ${passRate.toFixed(1)}% (${suite.passedTests}/${suite.totalTests})</p>
                    </div>
                </div>
              `;
            }).join('')}
        </div>
        
        <div class="timestamp">
            Generated on ${new Date().toLocaleString()}
        </div>
    </div>
</body>
</html>`;

    writeFileSync(join(process.cwd(), 'cart-test-report.html'), html);
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  const runner = new CartTestRunner();
  runner.runAllCartTests().catch(console.error);
}

export { CartTestRunner };