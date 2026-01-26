import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboardIcon,
  UsersIcon,
  PackageIcon,
  ShoppingCartIcon,
  BarChart3Icon,
  BellIcon,
  MenuIcon,
  LogOutIcon,
  TagIcon,
  GlobeIcon,
  EditIcon,
  FolderIcon,
  HashIcon,
  MessageSquareIcon,
  BoxesIcon,
  Percent,
  MapPinIcon,
  ArrowUpDownIcon,
  TrendingUpIcon,
  TruckIcon
} from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

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
    { title: 'Dashboard', path: '/admin', icon: <LayoutDashboardIcon size={20} /> },
    { title: 'Orders', path: '/admin/orders', icon: <ShoppingCartIcon size={20} /> },
    { title: 'Products', path: '/admin/products', icon: <PackageIcon size={20} /> },
    { title: 'Variants', path: '/admin/variants', icon: <TagIcon size={20} /> },
    { title: 'Users', path: '/admin/users', icon: <UsersIcon size={20} /> },
    { title: 'Shipping Methods', path: '/admin/shipping-methods', icon: <TruckIcon size={20} /> },
    { title: 'Tax Rates', path: '/admin/tax-rates', icon: <Percent size={20} /> },
    { title: 'Inventory', path: '/admin/inventory', icon: <BoxesIcon size={20} /> },
    { title: 'Locations', path: '/admin/inventory/locations', icon: <MapPinIcon size={20} /> },
    { title: 'Adjustments', path: '/admin/inventory/adjustments', icon: <ArrowUpDownIcon size={20} /> },
    { title: 'Website', path: '/', icon: <GlobeIcon size={20} /> },
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
        className={`fixed top-0 left-0 z-30 h-full w-64 bg-surface border-r border-border-light transition-transform duration-300 transform flex flex-col ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}>
        <div className="p-4 border-b border-border-light">
          <Link 
            to="/admin" 
            className="flex items-center cursor-pointer hover:opacity-80 transition-opacity"
            aria-label="Navigate to admin home page"
          >
            <img src="/banwee_logo_green.png" alt="Banwee Logo" className="h-8 mr-2" />
            <span className="text-xl font-semibold text-main">Admin</span>
          </Link>
        </div>
        <div className="py-4 flex-1 overflow-y-auto">
          <nav>
            <ul className="space-y-1">
              {menuItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center px-4 py-2.5 text-sm ${isActive(item.path)
                        ? 'bg-primary text-white font-medium'
                        : 'text-copy-light hover:bg-background'
                      }`}
                    onClick={() => setSidebarOpen(false)}>
                    <span className="mr-3">{item.icon}</span>
                    <span>{item.title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border-light bg-surface">
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md">
            <LogOutIcon size={18} className="mr-3" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 md:ml-64">
        {/* Header */}
        <header className="bg-surface border-b border-border-light sticky top-0 z-10">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center">
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 mr-3 md:hidden">
                <MenuIcon size={24} />
              </button>
              <h1 className="text-xl font-semibold text-main hidden md:block">
                {menuItems.find((item) => isActive(item.path))?.title || 'Admin'}
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* User */}
              <div className="flex items-center">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                  {(user as any)?.full_name?.charAt(0) || (user as any)?.firstname?.charAt(0) || 'A'}
                </div>
                <span className="ml-2 text-sm font-medium hidden md:block">
                  {(user as any)?.full_name || `${(user as any)?.firstname} ${(user as any)?.lastname}` || 'Admin'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
};