import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchIcon, FilterIcon, XIcon } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { ProductsAPI, CategoriesAPI } from '../api';
import { ProductCard } from '../components/product/ProductCard';
import { SkeletonProductCard } from '../components/ui/SkeletonProductCard';
import { Select } from '../components/ui/Select';
import { Dropdown } from '../components/ui/Dropdown';
import { themeClasses, combineThemeClasses, getInputClasses, getButtonClasses } from '../utils/themeClasses';
import { cn } from '../utils/utils';

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    searchParams.get('category')?.split(',') || []
  );
  const [sortOption, setSortOption] = useState('created_at:desc');
  const [priceRange, setPriceRange] = useState([0, 1000]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [productsData, setProductsData] = useState<any>(null);
  const [categories, setCategories] = useState<any[]>([]);

  const { loading, error, execute: fetchProducts } = useAsync({
    showErrorToast: false, // Disable error toasts
    showSuccessToast: false, // Disable success toasts
    onError: (error) => {
      // Log error to console instead of showing toast
      console.error('Failed to fetch products:', error);
    }
  });
  
  const { execute: fetchCategories } = useAsync({
    showErrorToast: false, // Disable error toasts
    showSuccessToast: false, // Disable success toasts
    onError: (error) => {
      // Log error to console instead of showing toast
      console.error('Failed to fetch categories:', error);
    }
  });

  // Fetch categories on component mount
  useEffect(() => {
    fetchCategories(async () => {
      const response = await CategoriesAPI.getCategories();
      setCategories(response.data?.categories || []);
      return response.data;
    });
  }, []); // Remove fetchCategories from dependencies to prevent repeat calls

  const sortOptions = [
    { value: 'created_at:desc', label: 'Newest First' },
    { value: 'created_at:asc', label: 'Oldest First' },
    { value: 'name:asc', label: 'Name A-Z' },
    { value: 'name:desc', label: 'Name Z-A' },
    { value: 'price:asc', label: 'Price Low to High' },
    { value: 'price:desc', label: 'Price High to Low' },
  ];

  // Fetch products when filters change
  useEffect(() => {
    const [sortBy, sortOrder] = sortOption.split(':');
    const params = {
      q: searchQuery || undefined,
      category: selectedCategories.length > 0 ? selectedCategories.join(',') : undefined,
      min_price: priceRange[0] > 0 ? priceRange[0] : undefined,
      max_price: priceRange[1] < 1000 ? priceRange[1] : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: currentPage,
      limit: 12,
    };

    fetchProducts(async () => {
      const response = await ProductsAPI.getProducts(params);
      setProductsData(response.data);
      return response.data;
    });
  }, [searchQuery, selectedCategories, sortOption, priceRange, currentPage]); // Remove fetchProducts from dependencies

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    const newParams = new URLSearchParams(searchParams);
    if (searchQuery) {
      newParams.set('q', searchQuery);
    } else {
      newParams.delete('q');
    }
    setSearchParams(newParams);
  };

  const handleCategoryChange = (categoryId: string) => {
    const newCategories = selectedCategories.includes(categoryId)
      ? selectedCategories.filter(id => id !== categoryId)
      : [...selectedCategories, categoryId];
    
    setSelectedCategories(newCategories);
    setCurrentPage(1);
    
    const newParams = new URLSearchParams(searchParams);
    if (newCategories.length > 0) {
      newParams.set('category', newCategories.join(','));
    } else {
      newParams.delete('category');
    }
    setSearchParams(newParams);
  };

  const handlePriceRangeChange = (newRange: [number, number]) => {
    setPriceRange(newRange);
    setCurrentPage(1);
    
    const newParams = new URLSearchParams(searchParams);
    if (newRange[0] > 0) {
      newParams.set('min_price', newRange[0].toString());
    } else {
      newParams.delete('min_price');
    }
    if (newRange[1] < 1000) {
      newParams.set('max_price', newRange[1].toString());
    } else {
      newParams.delete('max_price');
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategories([]);
    setPriceRange([0, 1000]);
    setSortOption('created_at:desc');
    setCurrentPage(1);
    setSearchParams({});
  };

  const retryFetch = () => {
    const [sortBy, sortOrder] = sortOption.split(':');
    const params = {
      q: searchQuery || undefined,
      category: selectedCategories.length > 0 ? selectedCategories.join(',') : undefined,
      min_price: priceRange[0] > 0 ? priceRange[0] : undefined,
      max_price: priceRange[1] < 1000 ? priceRange[1] : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: currentPage,
      limit: 12,
    };

    fetchProducts(async () => {
      const response = await ProductsAPI.getProducts(params);
      setProductsData(response.data);
      return response.data;
    });
  };

  // Don't show error UI, just log to console and show skeleton
  const shouldShowSkeleton = loading || (error && !productsData);

  const products = productsData?.data || [];
  const totalProducts = productsData?.total || 0;
  const totalPages = Math.ceil(totalProducts / 12);

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-xl font-semibold text-main dark:text-white mb-2">
          Products
        </h1>
        <p className="text-sm text-copy-light dark:text-gray-400">
          {loading && !productsData ? 'Loading products...' : `${totalProducts} products available`}
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" size={20} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                'w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600',
                'bg-white dark:bg-gray-800 text-gray-900 dark:text-white',
                'placeholder-gray-500 dark:placeholder-gray-400',
                'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary',
                'transition-colors'
              )}
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-lg font-medium transition-colors"
          >
            Search
          </button>
        </form>

        {/* Filter Toggle and Sort */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-gray-300 dark:border-gray-600',
              'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300',
              'hover:border-primary hover:bg-gray-50 dark:hover:bg-gray-700',
              'transition-colors font-medium'
            )}
          >
            <FilterIcon size={16} />
            <span>Filters</span>
            {(selectedCategories.length > 0 || priceRange[0] > 0 || priceRange[1] < 1000) && (
              <span className="bg-primary text-white text-xs px-2 py-0.5 rounded-full">
                {selectedCategories.length + (priceRange[0] > 0 || priceRange[1] < 1000 ? 1 : 0)}
              </span>
            )}
          </button>

          {/* Custom Sort Dropdown */}
          <div className="w-full sm:w-auto sm:min-w-[180px]">
            <Dropdown
              options={sortOptions}
              value={sortOption}
              onChange={setSortOption}
              placeholder="Sort by"
              className="w-full"
            />
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
            {/* Categories */}
            {categories && categories.length > 0 && (
              <div>
                <h3 className="text-base font-medium text-main dark:text-white mb-3">
                  Categories
                </h3>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => handleCategoryChange(category.id)}
                      className={cn(
                        'px-3 py-1.5 rounded-full text-sm transition-all duration-200',
                        selectedCategories.includes(category.id)
                          ? 'bg-primary text-white shadow-sm'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      )}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Price Range */}
            <div>
              <h3 className="text-base font-medium text-main dark:text-white mb-3">
                Price Range
              </h3>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="block text-xs text-copy-light dark:text-gray-400 mb-1">
                    Min Price
                  </label>
                  <input
                    type="number"
                    placeholder="0"
                    value={priceRange[0]}
                    onChange={(e) => handlePriceRangeChange([parseInt(e.target.value) || 0, priceRange[1]])}
                    className={cn(
                      'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600',
                      'bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm',
                      'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary'
                    )}
                  />
                </div>
                <span className="text-copy-light dark:text-gray-400 mt-5">—</span>
                <div className="flex-1">
                  <label className="block text-xs text-copy-light dark:text-gray-400 mb-1">
                    Max Price
                  </label>
                  <input
                    type="number"
                    placeholder="1000"
                    value={priceRange[1]}
                    onChange={(e) => handlePriceRangeChange([priceRange[0], parseInt(e.target.value) || 1000])}
                    className={cn(
                      'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600',
                      'bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm',
                      'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary'
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Clear Filters */}
            <button
              onClick={clearFilters}
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm rounded-lg',
                'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
                'hover:bg-gray-200 dark:hover:bg-gray-600',
                'transition-colors font-medium'
              )}
            >
              <XIcon size={16} />
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Products Grid - Better responsive layout */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3 sm:gap-4 lg:gap-6">
        {shouldShowSkeleton ? (
          // Show skeleton cards while loading or on error
          Array.from({ length: 20 }).map((_, index) => (
            <SkeletonProductCard key={index} />
          ))
        ) : products.length > 0 ? (
          // Show actual products
          products.map((product: any) => (
            <ProductCard 
              key={product.id} 
              product={product} 
              selectedVariant={product.variants?.[0] || product}
              className=""
              subscriptionId=""
            />
          ))
        ) : (
          // Show empty state - Theme responsive
          <div className="col-span-full text-center py-12 sm:py-16">
            <div className="max-w-md mx-auto">
              <div className={combineThemeClasses(
                themeClasses.background.elevated,
                themeClasses.border.default,
                'w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center border'
              )}>
                <SearchIcon size={24} className={themeClasses.text.muted} />
              </div>
              <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg mb-2')}>
                No products found
              </h3>
              <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-4')}>
                Try adjusting your search or filter criteria
              </p>
              <button
                onClick={clearFilters}
                className={combineThemeClasses(
                  getButtonClasses('primary'),
                  'transition-all duration-200 hover:scale-105'
                )}
              >
                Clear filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Pagination - Always show when there are products */}
      {products.length > 0 && (
        <div className="mt-8 sm:mt-12 flex justify-center">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className={cn(
                'px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                currentPage === 1
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                  : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              )}
            >
              Previous
            </button>
            
            <div className="flex items-center gap-1 sm:gap-2">
              {/* Show page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                if (pageNum > totalPages) return null;
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={cn(
                      'px-3 py-2 rounded-lg text-sm font-medium transition-colors min-w-[40px]',
                      currentPage === pageNum
                        ? 'bg-primary text-white'
                        : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className={cn(
                'px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                currentPage === totalPages
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                  : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Loading indicator for pagination */}
      {loading && productsData && (
        <div className="fixed bottom-4 right-4 bg-primary text-white px-4 py-2 rounded-lg shadow-lg z-50">
          <div className="flex items-center gap-2">
            <div className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4"></div>
            <span className="text-sm font-medium">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;