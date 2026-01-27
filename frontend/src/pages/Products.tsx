import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchIcon, FilterIcon, XIcon } from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { ProductsAPI, CategoriesAPI } from '../apis';
import { ProductCard } from '../components/ProductCard';
import { SkeletonProductCard } from '../components/ui/SkeletonProductCard';
import { Select } from '../components/ui/Select';
import { themeClasses, combineThemeClasses, getInputClasses, getButtonClasses } from '../lib/themeClasses';

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
  }, [fetchCategories]);

  const sortOptions = [
    { value: 'created_at:desc', label: 'Newest First' },
    { value: 'created_at:asc', label: 'Oldest First' },
    { value: 'name:asc', label: 'Name A-Z' },
    { value: 'name:desc', label: 'Name Z-A' },
    { value: 'price:asc', label: 'Price Low to High' },
    { value: 'price:desc', label: 'Price High to Low' },
  ];

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
      limit: 20,
    };

    fetchProducts(async () => {
      const response = await ProductsAPI.getProducts(params);
      setProductsData(response.data);
      return response.data;
    });
  }, [searchQuery, selectedCategories, sortOption, priceRange, currentPage, fetchProducts]);

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
      limit: 20,
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
  const totalPages = Math.ceil(totalProducts / 20);

  return (
    <div className={combineThemeClasses(themeClasses.layout.container, 'py-4 sm:py-8')}>
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl sm:text-3xl lg:text-4xl mb-2')}>
          Products
        </h1>
        <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm sm:text-base')}>
          {loading && !productsData ? 'Loading products...' : `${totalProducts} products available`}
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 sm:mb-8 space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <SearchIcon className={combineThemeClasses(themeClasses.text.muted, 'absolute left-3 top-1/2 transform -translate-y-1/2')} size={20} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={combineThemeClasses(
                getInputClasses('default'),
                'pl-10 pr-4 py-2.5 sm:py-3 text-sm sm:text-base'
              )}
            />
          </div>
          <button
            type="submit"
            className={combineThemeClasses(
              getButtonClasses('primary'),
              'px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base whitespace-nowrap'
            )}
          >
            Search
          </button>
        </form>

        {/* Filter Toggle and Sort */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={combineThemeClasses(
              getButtonClasses('outline'),
              'flex items-center gap-2 text-sm sm:text-base'
            )}
          >
            <FilterIcon size={16} />
            <span>Filters</span>
            {(selectedCategories.length > 0 || priceRange[0] > 0 || priceRange[1] < 1000) && (
              <span className={combineThemeClasses(themeClasses.background.primary, themeClasses.text.inverse, 'text-xs px-2 py-0.5 rounded-full')}>
                {selectedCategories.length + (priceRange[0] > 0 || priceRange[1] < 1000 ? 1 : 0)}
              </span>
            )}
          </button>

          {/* Custom Sort Select */}
          <div className="w-full sm:w-auto sm:min-w-[180px]">
            <Select
              options={sortOptions}
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              size="md"
              fullWidth
            />
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className={combineThemeClasses(
            themeClasses.card.base,
            'p-4 sm:p-6 space-y-4 sm:space-y-6'
          )}>
            {/* Categories */}
            {categories && categories.length > 0 && (
              <div>
                <h3 className={combineThemeClasses(themeClasses.text.heading, 'mb-3 text-sm sm:text-base')}>
                  Categories
                </h3>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => handleCategoryChange(category.id)}
                      className={combineThemeClasses(
                        'px-3 py-1.5 rounded-full text-sm transition-all duration-200',
                        selectedCategories.includes(category.id)
                          ? combineThemeClasses(themeClasses.background.primary, themeClasses.text.inverse, themeClasses.shadow.sm)
                          : combineThemeClasses(themeClasses.background.elevated, themeClasses.text.secondary, themeClasses.interactive.hover)
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
              <h3 className={combineThemeClasses(themeClasses.text.heading, 'mb-3 text-sm sm:text-base')}>
                Price Range
              </h3>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className={combineThemeClasses(themeClasses.text.muted, 'block text-xs mb-1')}>
                    Min Price
                  </label>
                  <input
                    type="number"
                    placeholder="0"
                    value={priceRange[0]}
                    onChange={(e) => setPriceRange([parseInt(e.target.value) || 0, priceRange[1]])}
                    className={combineThemeClasses(getInputClasses('default'), 'text-sm')}
                  />
                </div>
                <span className={combineThemeClasses(themeClasses.text.muted, 'mt-5')}>—</span>
                <div className="flex-1">
                  <label className={combineThemeClasses(themeClasses.text.muted, 'block text-xs mb-1')}>
                    Max Price
                  </label>
                  <input
                    type="number"
                    placeholder="1000"
                    value={priceRange[1]}
                    onChange={(e) => setPriceRange([priceRange[0], parseInt(e.target.value) || 1000])}
                    className={combineThemeClasses(getInputClasses('default'), 'text-sm')}
                  />
                </div>
              </div>
            </div>

            {/* Clear Filters */}
            <button
              onClick={clearFilters}
              className={combineThemeClasses(
                'flex items-center gap-2 text-sm transition-colors',
                themeClasses.text.secondary,
                themeClasses.interactive.hover
              )}
            >
              <XIcon size={16} />
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Products Grid - Theme responsive with smaller cards */}
      <div className={combineThemeClasses(
        'grid gap-2 sm:gap-3 lg:gap-4',
        'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8'
      )}>
        {shouldShowSkeleton ? (
          // Show skeleton cards while loading or on error
          Array.from({ length: 20 }).map((_, index) => (
            <SkeletonProductCard key={index} />
          ))
        ) : products.length > 0 ? (
          // Show actual products
          products.map((product: any) => (
            <ProductCard key={product.id} product={product} />
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

      {/* Pagination */}
      {totalPages > 1 && !loading && (
        <div className="mt-8 sm:mt-12 flex justify-center">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className={combineThemeClasses(
                getButtonClasses('outline'),
                'px-3 sm:px-4 py-2 text-sm sm:text-base'
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
                    className={combineThemeClasses(
                      'px-3 py-2 rounded-lg text-sm sm:text-base transition-colors',
                      currentPage === pageNum
                        ? combineThemeClasses(themeClasses.background.primary, themeClasses.text.inverse)
                        : combineThemeClasses(themeClasses.interactive.hover, themeClasses.text.primary)
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
              className={combineThemeClasses(
                getButtonClasses('outline'),
                'px-3 sm:px-4 py-2 text-sm sm:text-base'
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Loading indicator for pagination */}
      {loading && productsData && (
        <div className={combineThemeClasses(
          themeClasses.background.primary,
          themeClasses.text.inverse,
          themeClasses.shadow.lg,
          'fixed bottom-4 right-4 px-4 py-2 rounded-lg z-50'
        )}>
          <div className="flex items-center gap-2">
            <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-4 h-4 border-copy-inverse border-t-transparent')}></div>
            <span className="text-sm font-medium">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;