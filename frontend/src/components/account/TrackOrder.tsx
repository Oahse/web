import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchIcon, PackageIcon } from 'lucide-react';

const TrackOrder = () => {
  const [orderNumber, setOrderNumber] = useState('');
  const navigate = useNavigate();

  const handleTrackOrder = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (orderNumber.trim()) {
      // Navigate to track order page with the order ID
      navigate(`/track-order/${orderNumber}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 md:p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
            <PackageIcon size={32} className="text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Track Your Order</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Enter your order number to view tracking details and order status
          </p>
        </div>

        <form onSubmit={handleTrackOrder} className="space-y-6">
          <div>
            <label htmlFor="orderNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Order Number
            </label>
            <input
              id="orderNumber"
              type="text"
              placeholder="Enter your order ID (e.g., 550e8400-e29b-41d4-a716-446655440000)"
              value={orderNumber}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOrderNumber(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              You can find your order number in your order confirmation email
            </p>
          </div>

          <button
            type="submit"
            className="w-full bg-primary text-white py-3 px-6 rounded-lg hover:bg-primary-dark transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <SearchIcon size={20} />
            Track Order
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            Already have an account?{' '}
            <button
              onClick={() => navigate('/account/orders')}
              className="text-primary hover:underline font-medium"
            >
              View all your orders
            </button>
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Need Help?</h2>
        <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
          <p>• Order tracking is available 24-48 hours after your order is placed</p>
          <p>• If you can&apos;t find your order number, check your email confirmation</p>
          <p>• For urgent inquiries, contact our support team</p>
        </div>
        <button
          onClick={() => navigate('/contact')}
          className="mt-4 text-primary hover:underline text-sm font-medium"
        >
          Contact Support →
        </button>
      </div>
    </div>
  );
};

export default TrackOrder;
