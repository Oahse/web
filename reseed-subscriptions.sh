#!/bin/bash

###############################################################################
# Banwee Subscription Reseeding Script
# This script reseeds subscription data to match the updated interface structure.
#
# Usage: ./reseed-subscriptions.sh [OPTIONS]
# Options:
#   --count NUM          Number of subscriptions to create (default: 25)
#   --clear-existing     Clear existing subscriptions before seeding
#   --help               Show this help message
###############################################################################

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔄 Banwee Subscription Reseeding Script"
echo "======================================="
echo ""

# Default values
COUNT=25
CLEAR_EXISTING=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --count)
            COUNT="$2"
            shift 2
            ;;
        --clear-existing)
            CLEAR_EXISTING="--clear-existing"
            shift
            ;;
        --help)
            echo "Usage: ./reseed-subscriptions.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --count NUM          Number of subscriptions to create (default: 25)"
            echo "  --clear-existing     Clear existing subscriptions before seeding"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./reseed-subscriptions.sh"
            echo "  ./reseed-subscriptions.sh --count 50"
            echo "  ./reseed-subscriptions.sh --count 30 --clear-existing"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "📊 Reseeding Configuration:"
echo "   Subscription Count: $COUNT"
if [[ -n "$CLEAR_EXISTING" ]]; then
    echo "   Clear Existing: Yes"
else
    echo "   Clear Existing: No"
fi
echo ""

# Verify that the Docker backend container is running
if ! docker-compose ps | grep -q "banwee_backend.*Up"; then
    echo "❌ Error: Docker containers are not running!"
    echo "   Please run './docker-start.sh' first"
    exit 1
fi

echo "🔄 Running subscription reseeding..."
echo ""

# Execute the reseeding script within the backend container
docker-compose exec -T backend python reseed_subscriptions.py --count $COUNT $CLEAR_EXISTING

echo ""
echo "✅ Subscription reseeding complete!"
echo ""
echo "🎯 Next Steps:"
echo "   1. Check your subscription data in the admin panel"
echo "   2. Test the subscription card component in the frontend"
echo "   3. Verify the billing summary displays correctly"
echo ""