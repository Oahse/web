import React, { useState } from 'react';
import { 
  SubscriptionProductCard, 
  AutoRenewToggle, 
  VariantSelector, 
  SubscriptionCard,
  ProductSelectionModal
} from '../components/subscription';
import { themeClasses, combineThemeClasses } from '../lib/themeClasses';

// Mock data for demonstration
const mockSubscription = {
  id: 'sub_123',
  plan_id: 'premium',
  status: 'active' as const,
  price: 29.99,
  currency: 'USD',
  billing_cycle: 'monthly' as const,
  auto_renew: true,
  next_billing_date: '2024-02-15',
  current_period_end: '2024-02-15',
  products: [
    {
      id: 'prod_1',
      name: 'Premium Coffee Beans',
      price: 15.99,
      image: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop',
      primary_image: { url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop' }
    },
    {
      id: 'prod_2',
      name: 'Organic Tea Selection',
      price: 12.99,
      image: 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300&h=300&fit=crop',
      primary_image: { url: 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300&h=300&fit=crop' }
    }
  ],
  created_at: '2024-01-01'
};

const mockProducts = [
  {
    id: 'prod_1',
    product_id: 'prod_1',
    product_name: 'Premium Coffee Beans',
    name: 'Premium Coffee Beans',
    price: 15.99,
    currency: 'USD',
    quantity: 2,
    primary_image: { url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop' },
    variant_name: 'Medium Roast',
    variant_id: 'var_1',
    stock: 25,
    sku: 'COFFEE-MED-001'
  },
  {
    id: 'prod_2',
    product_id: 'prod_2',
    product_name: 'Organic Tea Selection',
    name: 'Organic Tea Selection',
    price: 12.99,
    currency: 'USD',
    quantity: 1,
    primary_image: { url: 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300&h=300&fit=crop' },
    variant_name: 'Earl Grey',
    variant_id: 'var_2',
    stock: 15,
    sku: 'TEA-EARL-001'
  }
];

const mockVariants: Array<{
  id: string;
  name: string;
  price: number;
  sale_price?: number;
  stock: number;
  sku?: string;
  images?: Array<{ url: string; is_primary?: boolean }>;
  primary_image?: { url: string };
  attributes?: { [key: string]: string };
}> = [
  {
    id: 'var_1',
    name: 'Light Roast',
    price: 14.99,
    sale_price: 12.99,
    stock: 30,
    sku: 'COFFEE-LIGHT-001',
    images: [{ url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop', is_primary: true }],
    attributes: { roast: 'Light', origin: 'Colombia' }
  },
  {
    id: 'var_2',
    name: 'Medium Roast',
    price: 15.99,
    stock: 25,
    sku: 'COFFEE-MED-001',
    images: [{ url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop', is_primary: true }],
    attributes: { roast: 'Medium', origin: 'Brazil' }
  },
  {
    id: 'var_3',
    name: 'Dark Roast',
    price: 16.99,
    stock: 5,
    sku: 'COFFEE-DARK-001',
    images: [{ url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop', is_primary: true }],
    attributes: { roast: 'Dark', origin: 'Ethiopia' }
  },
  {
    id: 'var_4',
    name: 'Espresso Blend',
    price: 18.99,
    stock: 0,
    sku: 'COFFEE-ESP-001',
    images: [{ url: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop', is_primary: true }],
    attributes: { roast: 'Dark', blend: 'Espresso' }
  }
];

export const SubscriptionDemo = () => {
  const [autoRenew, setAutoRenew] = useState(true);
  const [selectedVariant, setSelectedVariant] = useState('var_2');
  const [showProductModal, setShowProductModal] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState(new Set(['var_1', 'var_2']));

  return (
    <div className="container mx-auto px-4 py-8 space-y-12">
      <div className="text-center mb-12">
        <h1 className={combineThemeClasses(themeClasses.text.heading, 'text-3xl font-bold mb-4')}>
          Enhanced Subscription UI Components
        </h1>
        <p className={combineThemeClasses(themeClasses.text.secondary, 'text-lg')}>
          Beautifully styled subscription components with variant images and auto-renew features
        </p>
      </div>

      {/* Subscription Card Demo */}
      <section>
        <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-6')}>
          Subscription Card
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SubscriptionCard
            subscription={mockSubscription}
            onUpdate={async (id, data) => {
              console.log('Update subscription:', id, data);
            }}
            onCancel={(id) => console.log('Cancel subscription:', id)}
            showActions={true}
            compact={false}
          />
          <SubscriptionCard
            subscription={{...mockSubscription, status: 'paused', auto_renew: false}}
            onUpdate={async (id, data) => {
              console.log('Update subscription:', id, data);
            }}
            onResume={(id) => console.log('Resume subscription:', id)}
            showActions={true}
            compact={false}
          />
        </div>
      </section>

      {/* Auto-Renew Toggle Demo */}
      <section>
        <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-6')}>
          Auto-Renew Toggle
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
            <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium mb-4')}>
              Small Size
            </h3>
            <AutoRenewToggle
              isEnabled={autoRenew}
              onToggle={setAutoRenew}
              nextBillingDate="2024-02-15"
              billingCycle="monthly"
              showDetails={true}
              size="sm"
            />
          </div>
          <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
            <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium mb-4')}>
              Medium Size
            </h3>
            <AutoRenewToggle
              isEnabled={autoRenew}
              onToggle={setAutoRenew}
              nextBillingDate="2024-02-15"
              billingCycle="monthly"
              showDetails={true}
              size="md"
            />
          </div>
          <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
            <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium mb-4')}>
              Large Size
            </h3>
            <AutoRenewToggle
              isEnabled={autoRenew}
              onToggle={setAutoRenew}
              nextBillingDate="2024-02-15"
              billingCycle="monthly"
              showDetails={true}
              size="lg"
            />
          </div>
        </div>
      </section>

      {/* Subscription Product Cards Demo */}
      <section>
        <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-6')}>
          Subscription Product Cards
        </h2>
        
        <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-medium mb-4')}>
          Grid View
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {mockProducts.map((product) => (
            <SubscriptionProductCard
              key={product.id}
              product={product}
              onRemove={(id) => console.log('Remove product:', id)}
              onQuantityChange={(id, quantity) => console.log('Change quantity:', id, quantity)}
              showActions={true}
              viewMode="grid"
            />
          ))}
        </div>

        <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-medium mb-4')}>
          List View
        </h3>
        <div className="space-y-4">
          {mockProducts.map((product) => (
            <SubscriptionProductCard
              key={product.id}
              product={product}
              onRemove={(id) => console.log('Remove product:', id)}
              onQuantityChange={(id, quantity) => console.log('Change quantity:', id, quantity)}
              showActions={true}
              viewMode="list"
            />
          ))}
        </div>
      </section>

      {/* Variant Selector Demo */}
      <section>
        <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-6')}>
          Variant Selector
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
            <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium mb-4')}>
              Grid Layout
            </h3>
            <VariantSelector
              variants={mockVariants}
              selectedVariantId={selectedVariant}
              onVariantSelect={(variant) => setSelectedVariant(variant.id)}
              currency="USD"
              showImages={true}
              showStock={true}
              showSku={true}
              layout="grid"
              size="md"
            />
          </div>
          
          <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
            <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium mb-4')}>
              List Layout
            </h3>
            <VariantSelector
              variants={mockVariants}
              selectedVariantId={selectedVariant}
              onVariantSelect={(variant) => setSelectedVariant(variant.id)}
              currency="USD"
              showImages={true}
              showStock={true}
              showSku={true}
              layout="list"
              size="md"
            />
          </div>
        </div>
      </section>

      {/* Product Selection Modal Demo */}
      <section>
        <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-6')}>
          Product Selection Modal
        </h2>
        <div className={combineThemeClasses(themeClasses.card.base, 'p-6 text-center')}>
          <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-4')}>
            Click the button below to open the product selection modal
          </p>
          <button
            onClick={() => setShowProductModal(true)}
            className={combineThemeClasses(
              'px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors duration-200'
            )}
          >
            Open Product Selection Modal
          </button>
          
          {selectedProducts.size > 0 && (
            <div className="mt-4">
              <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                Selected products: {Array.from(selectedProducts).join(', ')}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Product Selection Modal */}
      <ProductSelectionModal
        isOpen={showProductModal}
        onClose={() => setShowProductModal(false)}
        onProductsSelected={(variantIds) => {
          setSelectedProducts(new Set(variantIds));
          console.log('Selected products:', variantIds);
        }}
        title="Select Products for Subscription"
        selectedProducts={selectedProducts}
        currency="USD"
      />
    </div>
  );
};