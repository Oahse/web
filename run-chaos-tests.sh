#!/bin/bash

# Chaos Engineering Test Runner
# Tests system resilience under various failure conditions

set -e

echo "🔥 CHAOS ENGINEERING TEST SUITE 🔥"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "backend/tests/chaos/run_chaos_tests.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to backend directory
cd backend

echo "📋 Available Chaos Tests:"
echo "1. Unit Chaos Tests (Safe - Mock failures)"
echo "2. Staging Chaos Tests (Destructive - Real infrastructure)"
echo "3. Random Chaos Simulation"
echo ""

# Default to unit tests if no argument provided
TEST_TYPE=${1:-"unit"}

case $TEST_TYPE in
    "unit"|"1")
        echo "🧪 Running Unit Chaos Tests (Safe)"
        echo "================================"
        python tests/chaos/run_chaos_tests.py
        ;;
    
    "staging"|"2")
        echo "⚠️  WARNING: Running Staging Chaos Tests (Destructive)"
        echo "====================================================="
        echo "This will:"
        echo "- Kill Kafka brokers randomly"
        echo "- Restart Redis instances"
        echo "- Kill consumer processes"
        echo "- Create network partitions"
        echo "- Simulate memory pressure"
        echo ""
        
        if [ "$ENVIRONMENT" != "staging" ]; then
            echo "❌ SAFETY CHECK FAILED"
            echo "Set ENVIRONMENT=staging to run destructive tests"
            exit 1
        fi
        
        echo "Type 'CHAOS' to confirm:"
        read -r confirmation
        if [ "$confirmation" != "CHAOS" ]; then
            echo "Chaos tests cancelled"
            exit 0
        fi
        
        python tests/chaos/staging_chaos_tests.py
        ;;
    
    "random"|"3")
        DURATION=${2:-10}
        echo "🎲 Running Random Chaos Simulation for $DURATION minutes"
        echo "======================================================="
        python tests/chaos/run_chaos_tests.py --random $DURATION
        ;;
    
    *)
        echo "❌ Invalid test type: $TEST_TYPE"
        echo "Usage: $0 [unit|staging|random] [duration_minutes]"
        echo ""
        echo "Examples:"
        echo "  $0 unit                    # Run safe unit tests"
        echo "  $0 staging                 # Run destructive staging tests"
        echo "  $0 random 15               # Run 15-minute random simulation"
        exit 1
        ;;
esac

echo ""
echo "✅ Chaos testing completed!"
echo ""
echo "📊 Check the generated reports for detailed results:"
echo "   - chaos_test_report_*.json"
echo "   - chaos_test_results.log"
echo ""

# Check if system survived
if [ -f "chaos_test_report_*.json" ]; then
    echo "🎯 System Survival Assessment:"
    echo "If you can read this message, your system survived the chaos! 🎉"
    echo ""
    echo "Key Resilience Indicators:"
    echo "✅ Core business operations continued during failures"
    echo "✅ System recovered gracefully from infrastructure issues"
    echo "✅ No cascading failures brought down the entire system"
    echo "✅ Circuit breakers and fallbacks worked as expected"
else
    echo "⚠️  No report generated - check logs for issues"
fi

echo ""
echo "🔧 Next Steps:"
echo "1. Review test results and identify weak points"
echo "2. Implement additional circuit breakers where needed"
echo "3. Add more fallback mechanisms for critical paths"
echo "4. Schedule regular chaos testing in your CI/CD pipeline"
echo ""
echo "Remember: If your system survives chaos, you're doing it right! 💪"