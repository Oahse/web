# Subscription Data Reseeding Guide

This guide explains how to reseed your subscription data to match the updated Subscription interface structure.

## Updated Subscription Interface

The new subscription interface includes the following structure:

```typescript
export interface Subscription {
  id: string;
  plan_id: string;
  status: 'active' | 'cancelled' | 'paused';
  price: number;
  currency: string;
  billing_cycle: 'weekly' | 'monthly' | 'yearly';
  auto_renew: boolean;
  next_billing_date?: string;
  created_at: string;
  products?: Array<{
    id: string;
    name: string;
    price: number;
    current_price?: number;
    image?: string;
  }>;
  variant_quantities?: { [variantId: string]: number };
  cost_breakdown?: {
    subtotal: number;
    shipping_cost: number;
    tax_amount: number;
    tax_rate: number;
    total_amount: number;
    currency: string;
    product_variants?: Array<{
      variant_id: string;
      name: string;
      price: number;
      quantity: number;
    }>;
  };
  shipping_cost?: number;
  tax_amount?: number;
  tax_rate?: number;
}
```

## Reseeding Options

### Option 1: Quick Reseed (Recommended)

Use the provided shell script for easy reseeding:

```bash
# Basic reseeding with 25 subscriptions
./reseed-subscriptions.sh

# Custom number of subscriptions
./reseed-subscriptions.sh --count 50

# Clear existing subscriptions and create new ones
./reseed-subscriptions.sh --count 30 --clear-existing
```

### Option 2: Python Script Direct

Run the Python script directly within the Docker container:

```bash
# Basic reseeding
docker-compose exec backend python reseed_subscriptions.py

# With options
docker-compose exec backend python reseed_subscriptions.py --count 50 --clear-existing
```

### Option 3: Full Database Reseed

If you want to reseed the entire database including subscriptions:

```bash
# This will recreate all data including subscriptions with the new structure
./seed-database.sh
```

## Testing the New Structure

After reseeding, you can test the subscription structure:

```bash
# Test the subscription data structure
docker-compose exec backend python test_subscription_structure.py
```

This will:
- Display sample subscription data
- Verify interface compliance
- Show the JSON structure for frontend testing
- Check cost breakdown completeness

## What's New in the Subscription Structure

### Enhanced Cost Breakdown
- **Detailed product variants**: Each subscription now includes detailed variant information
- **Proper tax calculation**: Tax is calculated on subtotal + shipping
- **Shipping cost tracking**: Separate shipping cost field
- **Currency support**: Multi-currency support throughout

### Improved Product Information
- **Products array**: Direct access to product information
- **Current pricing**: Support for current vs. base pricing
- **Product images**: Image URLs for better UI display

### Better Billing Management
- **Next billing date**: Accurate next billing date calculation
- **Status-aware billing**: Billing dates only for active subscriptions
- **Cycle-specific calculations**: Proper date calculation per billing cycle

## Frontend Integration

The subscription card component has been updated to display:

1. **Product and Variant Names**: Both product and variant information
2. **Detailed Cost Breakdown**: Itemized billing summary
3. **Quantity Information**: Clear quantity display for each variant
4. **Total Calculations**: Proper total calculation per variant

### Key Display Improvements

- **Billing Summary**: Renamed from "Cost Breakdown" for clarity
- **Subscription Items**: Better labeling for products
- **Shipping & Handling**: More descriptive shipping cost label
- **Total per Billing Cycle**: Context-aware total display

## Troubleshooting

### No Subscriptions Created
If no subscriptions are created, ensure you have:
1. Users in the database
2. Products and variants in the database
3. Docker containers running

### Missing Product Information
If products don't display properly:
1. Check that products have proper relationships to variants
2. Verify product images are properly seeded
3. Ensure variant-to-product relationships are correct

### Cost Calculation Issues
If cost calculations seem incorrect:
1. Verify tax rates are reasonable (5-12%)
2. Check shipping costs are within expected range
3. Ensure currency codes are valid

## Database Schema Updates

The subscription model now includes:
- `shipping_cost` field (replaces old shipping field names)
- `tax_amount` field (replaces old tax field names)
- Enhanced `cost_breakdown` JSON structure
- Proper `next_billing_date` calculation
- Multi-currency support

## Next Steps

After reseeding:

1. **Test the Frontend**: Check the subscription card component
2. **Verify API Responses**: Ensure API returns match the interface
3. **Test Billing Logic**: Verify billing calculations are correct
4. **Check Admin Panel**: Confirm admin views work with new structure

## Support

If you encounter issues:
1. Check Docker containers are running: `docker-compose ps`
2. View logs: `docker-compose logs backend`
3. Test database connection: `docker-compose exec backend python -c "from core.database import db_manager; print('DB OK')"`

The reseeding process ensures your subscription data matches the updated interface structure and provides a better user experience in the frontend application.