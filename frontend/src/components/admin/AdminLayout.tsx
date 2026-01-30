import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../store/AuthContext';
import { useTheme } from '../../store/ThemeContext';
import { ErrorBoundary } from '../ErrorBoundary';
import {
  LayoutDashboardIcon,
  UsersIcon,
  PackageIcon,
  ShoppingCartIcon,
  BarChart3Icon,
  MenuIcon,
  LogOutIcon,
  Percent,
  TruckIcon,
  BoxesIcon,
  SettingsIcon,
  FileTextIcon,
  TrendingUpIcon,
  GlobeIcon,
  UserIcon,
  ChevronDownIcon
} from 'lucide-react';

interface AdminLayoutProps {
  children?: React.ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { theme } = useTheme();

  // Check if user has admin access (additional security check)
  useEffect(() => {
    // Wait for auth check to complete
    if (isLoading) return;

    // If authenticated but not admin or supplier, redirect to home
    if (user && (user as any).role !== 'Admin' && (user as any).role !== 'Supplier') {
      navigate('/', { replace: true });
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  const menuItems = [
    { title: 'Dashboard', path: '/admin', icon: <LayoutDashboardIcon size={18} /> },
    { title: 'Orders', path: '/admin/orders', icon: <ShoppingCartIcon size={18} /> },
    { title: 'Products', path: '/admin/products', icon: <PackageIcon size={18} /> },
    { title: 'Users', path: '/admin/users', icon: <UsersIcon size={18} /> },
    { title: 'Subscriptions', path: '/admin/subscriptions', icon: <FileTextIcon size={18} /> },
    { title: 'Shipping', path: '/admin/shipping-methods', icon: <TruckIcon size={18} /> },
    { title: 'Tax Rates', path: '/admin/tax-rates', icon: <Percent size={18} /> },
    { title: 'Inventory', path: '/admin/inventory', icon: <BoxesIcon size={18} /> },
    { title: 'Website', path: '/', icon: <GlobeIcon size={18} /> },
  ];

  const isActive = (path: string) => {
    if (path === '/admin') {
      return location.pathname === '/admin';
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    (logout as any)();
    navigate('/');
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-copy-light">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex text-copy">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}></div>
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-30 h-full w-56 transition-transform duration-300 transform flex flex-col ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          } ${theme === 'dark' ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'} border-r`}>
        {/* Logo */}
        <div className={`p-3 border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
          <Link 
            to="/admin" 
            className="flex items-center cursor-pointer hover:opacity-80 transition-opacity"
            aria-label="Navigate to admin home page"
          >
            <img src="/banwee_logo_green.png" alt="Banwee Logo" className="h-6 mr-2" />
            <span className={`text-base font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Admin</span>
          </Link>
        </div>
        <div className="py-3 flex-1 overflow-y-auto">
          <nav>
            <ul className="space-y-1">
              {menuItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center px-3 py-2 text-xs ${isActive(item.path)
                        ? 'bg-blue-600 text-white font-medium'
                        : theme === 'dark' ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    onClick={() => setSidebarOpen(false)}>
                    <span className="mr-2">{item.icon}</span>
                    <span>{item.title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className={`absolute bottom-0 left-0 right-0 p-3 border-t ${theme === 'dark' ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'}`}>
          <button
            onClick={handleLogout}
            className={`flex items-center w-full px-3 py-2 text-xs rounded-md ${
              theme === 'dark' 
                ? 'text-red-400 hover:bg-red-900/20' 
                : 'text-red-600 hover:bg-red-50'
            }`}>
            <LogOutIcon size={14} className="mr-2" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 md:ml-56">
        {/* Header */}
        <header className={`sticky top-0 z-10 ${theme === 'dark' ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'} border-b`}>
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center">
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 mr-3 md:hidden">
                <MenuIcon size={20} />
              </button>
              <h1 className={`text-lg font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'} hidden md:block`}>
                {menuItems.find((item) => isActive(item.path))?.title || 'Admin'}
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* User Profile Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${
                    theme === 'dark' 
                      ? 'border-gray-600 bg-gray-800 text-white hover:bg-gray-700' 
                      : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                    {(user as any)?.full_name?.charAt(0) || (user as any)?.firstname?.charAt(0) || 'A'}
                  </div>
                  <span className="text-sm font-medium hidden md:block">
                    {(user as any)?.full_name || `${(user as any)?.firstname} ${(user as any)?.lastname}` || 'Admin'}
                  </span>
                  <ChevronDownIcon size={16} />
                </button>
                
                {profileDropdownOpen && (
                  <div className={`absolute right-0 mt-2 w-48 rounded-lg border shadow-lg z-50 ${
                    theme === 'dark' 
                      ? 'bg-gray-800 border-gray-700' 
                      : 'bg-white border-gray-200'
                  }`}>
                    <Link
                      to="/account/profile"
                      className={`block px-4 py-2 text-sm ${
                        theme === 'dark' 
                          ? 'text-gray-300 hover:bg-gray-700' 
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setProfileDropdownOpen(false)}
                    >
                      <div className="flex items-center space-x-2">
                        <UserIcon size={16} />
                        <span>Profile</span>
                      </div>
                    </Link>
                    <Link
                      to="/account"
                      className={`block px-4 py-2 text-sm ${
                        theme === 'dark' 
                          ? 'text-gray-300 hover:bg-gray-700' 
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setProfileDropdownOpen(false)}
                    >
                      <div className="flex items-center space-x-2">
                        <LayoutDashboardIcon size={16} />
                        <span>My Account</span>
                      </div>
                    </Link>
                    <div className={`border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}></div>
                    <button
                      onClick={() => {
                        handleLogout();
                        setProfileDropdownOpen(false);
                      }}
                      className={`block w-full text-left px-4 py-2 text-sm ${
                        theme === 'dark' 
                          ? 'text-red-400 hover:bg-red-900/20' 
                          : 'text-red-600 hover:bg-red-50'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <LogOutIcon size={16} />
                        <span>Logout</span>
                      </div>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6">
          <ErrorBoundary>
            {children || <Outlet />}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;