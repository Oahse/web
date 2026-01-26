import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchIcon, FilterIcon, XIcon } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { ProductsAPI } from '../apis';
import { ProductCard } from '../components/ProductCard';
import { Loading } from '../components/Loading';
import { Error } from '../components/Error';
import { useCategories } from '../contexts/CategoryContext';

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [selectedCategories, setSelectedCategories] = useState(
    searchParams.get('category')?.split(',') || []
  );
  const [sortOption, setSortOption] = useState('created_at:desc');
  const [priceRange, setPriceRange] = useState([0, 1000]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const { data: productsData, loading, error, execute: fetchProducts } = useApi();
  const { categories } = useCategories();

  const buildSearchParams = useCallback(() => {
    const [sortBy, sortOrder] = sortOption.split(':');
    return {
      q: searchQuery || undefined,
      category: selectedCategories.length > 0 ? selectedCategories.join(',') : undefined,
      min_price: priceRange[0] > 0 ? priceRange[0] : undefined,
      max_price: priceRange[1] < 1000 ? priceRange[1] : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: currentPage,
      limit: 20,
    };
  }, [searchQuery, selectedCategories, sortOption, priceRange, currentPage]);

  useEffect(() => {
    const params = buildSearchParams();
    fetchProducts(() => ProductsAPI.getProducts(params));
  }, [buildSearchParams, fetchProducts]);

  const handleSearch = (e) => {
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

  const handleCategoryChange = (categoryId) => {
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

  if (loading && !productsData) {
    return <Loading text="Loading products..." />;
  }

  if (error && !productsData) {
    return <Error message="Failed to load products" onRetry={() => fetchProducts(() => ProductsAPI.getProducts(buildSearchParams()))} />;
  }

  const products = productsData?.items || [];
  const totalProducts = productsData?.total || 0;
  const totalPages = Math.ceil(totalProducts / 20);

  return (
    <div className="max-w-7xl mx-auto px-4 py-4 sm:py-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="heading text-2xl sm:text-3xl mb-2">Products</h1>
        <p className="body-text text-gray-600">{totalProducts} products available</p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
          >
            Search
          </button>
        </form>

        {/* Filter Toggle */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <FilterIcon size={16} />
            <span className="button-text">Filters</span>
          </button>

          <select
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
          >
            <option value="created_at:desc">Newest First</option>
            <option value="created_at:asc">Oldest First</option>
            <option value="name:asc">Name A-Z</option>
            <option value="name:desc">Name Z-A</option>
            <option value="price:asc">Price Low to High</option>
            <option value="price:desc">Price High to Low</option>
          </select>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
            {/* Categories */}
            {categories && categories.length > 0 && (
              <div>
                <h3 className="heading text-sm font-medium mb-2">Categories</h3>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => handleCategoryChange(category.id)}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        selectedCategories.includes(category.id)
                          ? 'bg-primary text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Price Range */}
            <div>
              <h3 className="heading text-sm font-medium mb-2">Price Range</h3>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={priceRange[0]}
                  onChange={(e) => setPriceRange([parseInt(e.target.value) || 0, priceRange[1]])}
                  className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={priceRange[1]}
                  onChange={(e) => setPriceRange([priceRange[0], parseInt(e.target.value) || 1000])}
                  className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                />
              </div>
            </div>

            {/* Clear Filters */}
            <button
              onClick={clearFilters}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
            >
              <XIcon size={16} />
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Products Grid */}
      {products.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="body-text text-gray-600">No products found</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex justify-center">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            
            <span className="px-4 py-2 text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {loading && productsData && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-3 py-2 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;