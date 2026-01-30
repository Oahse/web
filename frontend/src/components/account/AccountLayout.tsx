import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { 
  User, 
  ShoppingBag, 
  Heart, 
  CreditCard, 
  Package, 
  Settings, 
  LogOut,
  Menu,
  X,
  ChevronRight,
  Home,
  FileText,
  MapPin
} from 'lucide-react';
import { useAuth } from '../../store/AuthContext';
import { cn } from '../../utils/cn';

interface AccountLayoutProps {
  children?: React.ReactNode;
}

const AccountLayout: React.FC<AccountLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/account',
      icon: Home,
      current: location.pathname === '/account'
    },
    {
      name: 'Profile',
      href: '/account/profile',
      icon: User,
      current: location.pathname === '/account/profile'
    },
    {
      name: 'Orders',
      href: '/account/orders',
      icon: Package,
      current: location.pathname.startsWith('/account/orders')
    },
    {
      name: 'Order Tracking',
      href: '/account/tracking',
      icon: MapPin,
      current: location.pathname === '/account/tracking'
    },
    {
      name: 'Wishlist',
      href: '/account/wishlist',
      icon: Heart,
      current: location.pathname === '/account/wishlist'
    },
    {
      name: 'Subscriptions',
      href: '/account/subscriptions',
      icon: CreditCard,
      current: location.pathname.startsWith('/account/subscriptions')
    },
    {
      name: 'Payment Methods',
      href: '/account/payment-methods',
      icon: CreditCard,
      current: location.pathname === '/account/payment-methods'
    },
    {
      name: 'Addresses',
      href: '/account/addresses',
      icon: MapPin,
      current: location.pathname === '/account/addresses'
    },
    {
      name: 'Settings',
      href: '/account/settings',
      icon: Settings,
      current: location.pathname === '/account/settings'
    }
  ];

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 lg:flex lg:flex-col",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Sidebar header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">My Account</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {navigationItems.map((item) => (
            <a
              key={item.name}
              href={item.href}
              onClick={(e) => {
                e.preventDefault();
                navigate(item.href);
              }}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                item.current
                  ? "bg-primary text-white"
                  : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
              {item.current && (
                <ChevronRight className="h-4 w-4 ml-auto" />
              )}
            </a>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 w-full px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <LogOut className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top bar */}
        <div className="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <Menu className="h-6 w-6" />
              </button>
              <div className="flex-1">
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {navigationItems.find(item => item.current)?.name || 'Account'}
                </h1>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          <div className="py-4">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children || <Outlet />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AccountLayout;
