#!/bin/bash

###############################################################################
# Banwee Database Seeding Script
# This script seeds the PostgreSQL database with comprehensive sample data.
# It leverages the 'init_db.py' script within the backend container.
#
# Usage: ./seed-database.sh [OPTIONS]
# Options:
#   --users NUM        Number of users to create (default: 150)
#   --products NUM     Number of products to create (default: 300)
#   --variants NUM     Variants per product (default: 3)
#   --batch-size NUM   Batch size for inserts (default: 50)
#   --help             Show this help message
###############################################################################

set -e  # Exit immediately if a command exits with a non-zero status

echo "🌱 Banwee Database Seeding Script"
echo "=================================="
echo ""

# Default values for seeding, can be overridden by command-line arguments
USERS=150
PRODUCTS=300
VARIANTS=3
BATCH_SIZE=50

# Parse command line arguments to customize seeding parameters
while [[ $# -gt 0 ]]; do
    case $1 in
        --users)
            USERS="$2"
            shift 2
            ;; 
        --products)
            PRODUCTS="$2"
            shift 2
            ;; 
        --variants)
            VARIANTS="$2"
            shift 2
            ;; 
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;; 
        --help)
            echo "Usage: ./seed-database.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --users NUM        Number of users to create (default: 150)"
            echo "  --products NUM     Number of products to create (default: 300)"
            echo "  --variants NUM     Variants per product (default: 3)"
            echo "  --batch-size NUM   Batch size for inserts (default: 50)"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./seed-database.sh"
            echo "  ./seed-database.sh --users 200 --products 500"
            echo "  ./seed-database.sh --batch-size 100"
            exit 0
            ;; 
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;; 
    esac
done

echo "📊 Seeding Configuration:"
echo "   Users:      $USERS"
echo "   Products:   $PRODUCTS"
echo "   Variants:   $VARIANTS per product"
echo "   Batch Size: $BATCH_SIZE"
echo ""

# Verify that the Docker backend container is running
if ! docker-compose ps | grep -q "banwee_backend.*Up"; then
    echo "❌ Error: Docker containers are not running!"
    echo "   Please run './docker-start.sh' first"
    exit 1
fi

echo "🔄 Initializing database tables..."
# Execute init_db.py within the backend container to create database tables.
# It relies on environment variables set in docker-compose.yml and backend/Dockerfile
# to connect to the PostgreSQL service.
docker-compose exec -T backend python init_db.py

echo ""
echo "🌱 Seeding database with sample data..."
echo "   This may take several minutes depending on the data size..."
echo ""

# Execute init_db.py with the --seed flag to populate the database with sample data.
# Parameters like --users, --products, etc., are passed from the script's arguments.
docker-compose exec -T backend python init_db.py --seed \
    --users $USERS \
    --products $PRODUCTS \
    --variants $VARIANTS \
    --batch-size $BATCH_SIZE

echo ""
echo "✅ Database seeding complete!"
echo ""
echo "📝 Test credentials have been saved to backend/users.txt"
echo ""
echo "🔐 Default Admin Account:"
echo "   Email:    admin@banwee.com"
echo "   Password: adminpass"
echo ""
echo "🏪 Default Supplier Account:"
echo "   Email:    supplier@banwee.com"
echo "   Password: supplierpass"
echo ""

echo "📊 Database Statistics:"
# Display statistics of the seeded data by querying the PostgreSQL database directly.
docker-compose exec -T postgres psql -U banwee -d banwee_db -c "
SELECT 
    'Users' as entity, COUNT(*) as count FROM users
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'Categories', COUNT(*) FROM categories
ORDER BY entity;
"

echo ""
echo "🎉 Your Banwee application is ready to use!"
echo "   Visit: http://localhost:5173"
echo ""