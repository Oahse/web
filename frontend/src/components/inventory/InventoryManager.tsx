import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { 
  PackageIcon, 
  AlertTriangleIcon, 
  TrendingDownIcon,
  SearchIcon,
  RefreshCwIcon,
  SettingsIcon,
  MailIcon,
  EditIcon,
  PlusIcon,
  MinusIcon,
  SaveIcon,
  XIcon
} from 'lucide-react';
import { stockMonitor, StockThreshold, StockAlert } from '../../services/stockMonitoring';
import { useAsync } from '../../hooks/useAsync';

interface InventoryItem {
  id: string;
  variant_id: string;
  product_id: string;
  product_name: string;
  variant_name: string;
  sku: string;
  current_stock: number;
  reserved_stock: number;
  available_stock: number;
  warehouse_location?: string;
  last_updated: string;
  images?: Array<{
    url: string;
    alt_text?: string;
    is_primary?: boolean;
  }>;
  base_price: number;
  sale_price?: number;
  low_stock_threshold?: number;
  critical_threshold?: number;
  out_of_stock_threshold?: number;
}

interface StockAdjustment {
  variant_id: string;
  adjustment_type: 'increase' | 'decrease' | 'set';
  quantity: number;
  reason: string;
  notes?: string;
}

export const InventoryManager: React.FC = () => {
  // ✅ Using useState for all local state management
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [filteredInventory, setFilteredInventory] = useState<InventoryItem[]>([]);
  const [stockAlerts, setStockAlerts] = useState<StockAlert[]>([]);
  const [stockThresholds, setStockThresholds] = useState<StockThreshold[]>([]);
  
  // Filter and search states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('product_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // UI states
  const [showAdjustmentModal, setShowAdjustmentModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [showAlertsPanel, setShowAlertsPanel] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [editingThresholds, setEditingThresholds] = useState<Record<string, boolean>>({});
  
  // Adjustment form state
  const [adjustment, setAdjustment] = useState<StockAdjustment>({
    variant_id: '',
    adjustment_type: 'increase',
    quantity: 0,
    reason: '',
    notes: ''
  });

  const { loading, error, execute: fetchData } = useAsync();

  // Fetch inventory data from API
  const fetchInventoryData = useCallback(async () => {
    try {
      const response = await fetch('/v1/inventories', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch inventory data');
      }
      
      const data = await response.json();
      return data.items || [];
    } catch (error) {
      console.error('Error fetching inventory:', error);
      throw error;
    }
  }, []);

  // Initialize data and stock monitoring
  useEffect(() => {
    fetchData(async () => {
      const inventoryData = await fetchInventoryData();
      setInventory(inventoryData);

      // Initialize stock monitoring for each item
      inventoryData.forEach((item: InventoryItem) => {
        stockMonitor.setStockThreshold(item.variant_id, {
          low_stock_threshold: item.low_stock_threshold || 10,
          critical_threshold: item.critical_threshold || 5,
          out_of_stock_threshold: item.out_of_stock_threshold || 0,
          email_notifications_enabled: true
        });

        stockMonitor.updateStock(
          item.variant_id,
          item.current_stock,
          item.product_name,
          item.variant_name
        );
      });

      // Get initial alerts and thresholds
      setStockAlerts(stockMonitor.getAllAlerts());
      setStockThresholds(stockMonitor.getAllThresholds());

      return inventoryData;
    });
  }, [fetchData, fetchInventoryData]);

  // Filter and sort inventory
  useEffect(() => {
    let filtered = [...inventory];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(item =>
        item.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.variant_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.sku.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(item => {
        const stockStatus = stockMonitor.getStockStatus(item.variant_id);
        return stockStatus.status === statusFilter;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy as keyof InventoryItem];
      let bValue: any = b[sortBy as keyof InventoryItem];

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    setFilteredInventory(filtered);
  }, [inventory, searchQuery, statusFilter, sortBy, sortOrder]);

  // Handle stock adjustment
  const handleStockAdjustment = async () => {
    if (!selectedItem) return;

    try {
      const response = await fetch(`/v1/inventories/${selectedItem.variant_id}/adjust`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(adjustment)
      });

      if (!response.ok) {
        throw new Error('Failed to adjust stock');
      }

      const updatedItem = await response.json();
      
      // Update local inventory
      const updatedInventory = inventory.map(item =>
        item.variant_id === selectedItem.variant_id
          ? { ...item, ...updatedItem }
          : item
      );
      setInventory(updatedInventory);

      // Update stock monitoring
      const alerts = stockMonitor.updateStock(
        selectedItem.variant_id,
        updatedItem.current_stock,
        selectedItem.product_name,
        selectedItem.variant_name
      );
      
      if (alerts.length > 0) {
        setStockAlerts(prev => [...alerts, ...prev]);
      }
      setStockThresholds(stockMonitor.getAllThresholds());

      toast.success(`Stock adjusted for ${selectedItem.product_name}`);
      setShowAdjustmentModal(false);
      setSelectedItem(null);
      setAdjustment({
        variant_id: '',
        adjustment_type: 'increase',
        quantity: 0,
        reason: '',
        notes: ''
      });
    } catch (error: any) {
      toast.error(error.message || 'Failed to adjust stock');
    }
  };

  // Handle threshold update
  const handleThresholdUpdate = async (variantId: string, thresholds: {
    low_stock_threshold: number;
    critical_threshold: number;
    out_of_stock_threshold: number;
  }) => {
    try {
      const response = await fetch(`/v1/inventories/${variantId}/thresholds`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(thresholds)
      });

      if (!response.ok) {
        throw new Error('Failed to update thresholds');
      }

      // Update local inventory
      const updatedInventory = inventory.map(item =>
        item.variant_id === variantId
          ? { ...item, ...thresholds }
          : item
      );
      setInventory(updatedInventory);

      // Update stock monitoring
      stockMonitor.setStockThreshold(variantId, {
        ...thresholds,
        email_notifications_enabled: true
      });
      setStockThresholds(stockMonitor.getAllThresholds());

      toast.success('Stock thresholds updated');
      setEditingThresholds(prev => ({ ...prev, [variantId]: false }));
    } catch (error: any) {
      toast.error(error.message || 'Failed to update thresholds');
    }
  };

  // Refresh data
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const inventoryData = await fetchInventoryData();
      setInventory(inventoryData);
      toast.success('Inventory data refreshed');
    } catch (error) {
      toast.error('Failed to refresh data');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Get stock status styling
  const getStockStatusStyle = (variantId: string) => {
    const status = stockMonitor.getStockStatus(variantId);
    const styles: Record<string, string> = {
      in_stock: 'bg-green-100 text-green-800',
      low_stock: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-orange-100 text-orange-800',
      out_of_stock: 'bg-red-100 text-red-800'
    };
    return styles[status.status] || 'bg-gray-100 text-gray-800';
  };

  // Get primary image
  const getPrimaryImage = (item: InventoryItem) => {
    if (!item.images || item.images.length === 0) {
      return '/placeholder-product.jpg';
    }
    const primaryImage = item.images.find(img => img.is_primary);
    return primaryImage?.url || item.images[0]?.url || '/placeholder-product.jpg';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="heading text-2xl mb-2">Inventory Management</h1>
            <p className="body-text text-gray-600">
              Monitor stock levels, adjust inventory, and manage thresholds
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAlertsPanel(true)}
              className="relative p-2 text-gray-600 hover:text-primary rounded-lg hover:bg-gray-100"
              title="View alerts"
            >
              <AlertTriangleIcon size={20} />
              {stockAlerts.filter(a => !a.acknowledged).length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {stockAlerts.filter(a => !a.acknowledged).length}
                </span>
              )}
            </button>
            
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50"
            >
              <RefreshCwIcon size={16} className={isRefreshing ? 'animate-spin' : ''} />
              <span className="button-text">Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <PackageIcon className="text-blue-500" size={24} />
            <div>
              <p className="body-text text-sm text-gray-600">Total Items</p>
              <p className="heading text-xl">{inventory.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <TrendingDownIcon className="text-red-500" size={24} />
            <div>
              <p className="body-text text-sm text-gray-600">Low Stock</p>
              <p className="heading text-xl">
                {stockThresholds.filter(t => t.status === 'low_stock' || t.status === 'critical').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <AlertTriangleIcon className="text-orange-500" size={24} />
            <div>
              <p className="body-text text-sm text-gray-600">Out of Stock</p>
              <p className="heading text-xl">
                {stockThresholds.filter(t => t.status === 'out_of_stock').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <MailIcon className="text-green-500" size={24} />
            <div>
              <p className="body-text text-sm text-gray-600">Alerts Sent</p>
              <p className="heading text-xl">
                {stockAlerts.filter(a => a.email_sent).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
          >
            <option value="all">All Status</option>
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="critical">Critical</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>

          {/* Sort */}
          <select
            value={`${sortBy}:${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split(':');
              setSortBy(field);
              setSortOrder(order as 'asc' | 'desc');
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
          >
            <option value="product_name:asc">Name A-Z</option>
            <option value="product_name:desc">Name Z-A</option>
            <option value="current_stock:asc">Stock Low-High</option>
            <option value="current_stock:desc">Stock High-Low</option>
            <option value="last_updated:desc">Recently Updated</option>
          </select>

          <div className="flex gap-2">
            <button
              onClick={() => {
                setSelectedItem(null);
                setShowAdjustmentModal(true);
              }}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark"
            >
              <span className="button-text">Bulk Adjust</span>
            </button>
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stock
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thresholds
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInventory.map((item) => {
                const stockStatus = stockMonitor.getStockStatus(item.variant_id);
                const isEditingThreshold = editingThresholds[item.variant_id];
                
                return (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <img
                          src={getPrimaryImage(item)}
                          alt={`${item.product_name} ${item.variant_name}`}
                          className="w-10 h-10 rounded-lg object-cover mr-3"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/placeholder-product.jpg';
                          }}
                        />
                        <div>
                          <div className="product-title text-sm font-medium text-gray-900">
                            {item.product_name}
                          </div>
                          <div className="body-text text-sm text-gray-500">
                            {item.variant_name}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="body-text text-sm text-gray-900">{item.sku}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">{item.current_stock}</div>
                        <div className="text-gray-500">Available: {item.available_stock}</div>
                        {item.reserved_stock > 0 && (
                          <div className="text-orange-600">Reserved: {item.reserved_stock}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStockStatusStyle(item.variant_id)}`}>
                        {stockStatus.message}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {isEditingThreshold ? (
                        <div className="space-y-1">
                          <input
                            type="number"
                            placeholder="Low"
                            defaultValue={item.low_stock_threshold || 10}
                            className="w-16 px-1 py-1 text-xs border rounded"
                            id={`low-${item.variant_id}`}
                          />
                          <input
                            type="number"
                            placeholder="Critical"
                            defaultValue={item.critical_threshold || 5}
                            className="w-16 px-1 py-1 text-xs border rounded"
                            id={`critical-${item.variant_id}`}
                          />
                          <div className="flex gap-1">
                            <button
                              onClick={() => {
                                const lowInput = document.getElementById(`low-${item.variant_id}`) as HTMLInputElement;
                                const criticalInput = document.getElementById(`critical-${item.variant_id}`) as HTMLInputElement;
                                handleThresholdUpdate(item.variant_id, {
                                  low_stock_threshold: parseInt(lowInput.value) || 10,
                                  critical_threshold: parseInt(criticalInput.value) || 5,
                                  out_of_stock_threshold: 0
                                });
                              }}
                              className="p-1 text-green-600 hover:bg-green-50 rounded"
                            >
                              <SaveIcon size={12} />
                            </button>
                            <button
                              onClick={() => setEditingThresholds(prev => ({ ...prev, [item.variant_id]: false }))}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                            >
                              <XIcon size={12} />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-gray-600">
                          <div>Low: {item.low_stock_threshold || 10}</div>
                          <div>Critical: {item.critical_threshold || 5}</div>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingThresholds(prev => ({ ...prev, [item.variant_id]: !prev[item.variant_id] }))}
                          className="text-primary hover:text-primary-dark"
                          title="Edit thresholds"
                        >
                          <SettingsIcon size={16} />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedItem(item);
                            setAdjustment(prev => ({ ...prev, variant_id: item.variant_id }));
                            setShowAdjustmentModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-800"
                          title="Adjust stock"
                        >
                          <EditIcon size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Adjustment Modal */}
      {showAdjustmentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="heading text-lg mb-4">
              {selectedItem ? `Adjust Stock: ${selectedItem.product_name}` : 'Bulk Stock Adjustment'}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Adjustment Type
                </label>
                <select
                  value={adjustment.adjustment_type}
                  onChange={(e) => setAdjustment(prev => ({ ...prev, adjustment_type: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                >
                  <option value="increase">Increase Stock</option>
                  <option value="decrease">Decrease Stock</option>
                  <option value="set">Set Stock Level</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  min="0"
                  value={adjustment.quantity}
                  onChange={(e) => setAdjustment(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason
                </label>
                <select
                  value={adjustment.reason}
                  onChange={(e) => setAdjustment(prev => ({ ...prev, reason: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                >
                  <option value="">Select reason...</option>
                  <option value="restock">Restock</option>
                  <option value="damaged">Damaged goods</option>
                  <option value="returned">Customer return</option>
                  <option value="correction">Inventory correction</option>
                  <option value="transfer">Warehouse transfer</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (Optional)
                </label>
                <textarea
                  value={adjustment.notes}
                  onChange={(e) => setAdjustment(prev => ({ ...prev, notes: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleStockAdjustment}
                disabled={!adjustment.reason || adjustment.quantity <= 0}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50"
              >
                Apply Adjustment
              </button>
              <button
                onClick={() => {
                  setShowAdjustmentModal(false);
                  setSelectedItem(null);
                  setAdjustment({
                    variant_id: '',
                    adjustment_type: 'increase',
                    quantity: 0,
                    reason: '',
                    notes: ''
                  });
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredInventory.length === 0 && (
        <div className="text-center py-12">
          <PackageIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="heading text-lg text-gray-900 mt-2">No inventory items found</h3>
          <p className="body-text text-gray-500 mt-1">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  );
};