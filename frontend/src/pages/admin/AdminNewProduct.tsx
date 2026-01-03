import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, PlusIcon, XIcon, UploadIcon, ChevronDownIcon } from 'lucide-react';
import { ProductsAPI, CategoriesAPI } from '../../apis';
import { useLocale } from '../../contexts/LocaleContext';
import { validatePriceInput, validateSalePrice, formatPriceForInput } from '../../lib/price-utils';
import { toast } from 'react-hot-toast';
import { uploadMultipleFiles } from '../../lib/github';
import { VariantCodeGenerator } from '../../components/product/VariantCodeGenerator';

interface ProductFormData {
  name: string;
  description: string;
  category_id: string;
  is_active: boolean;
}

interface VariantFormData {
  name: string;
  base_price: string;
  sale_price: string;
  stock: string;
  attributes: Record<string, string>;
  images: File[];
  imagePreviewUrls: string[];
  imageUrls: string[]; // jsDelivr CDN URLs
  tempId?: string; // Temporary ID for tracking before creation
  createdVariantId?: string; // Actual variant ID after creation
  hasCodes?: boolean; // Track if codes have been generated
}

interface Category {
  id: string;
  name: string;
  description?: string;
}

export const AdminNewProduct = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  
  const [productData, setProductData] = useState<ProductFormData>({
    name: '',
    description: '',
    category_id: '',
    is_active: true,
  });

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setLoadingCategories(true);
        const response = await CategoriesAPI.getCategories();
        const categoriesData = response?.data || response || [];
        setCategories(categoriesData);
      } catch (error) {
        console.error('Error fetching categories:', error);
        toast.error('Failed to load categories');
      } finally {
        setLoadingCategories(false);
      }
    };

    fetchCategories();
  }, []);

  const [variants, setVariants] = useState<VariantFormData[]>([
    {
      name: 'Default',
      base_price: '',
      sale_price: '',
      stock: '',
      attributes: {},
      images: [],
      imagePreviewUrls: [],
      imageUrls: [],
      tempId: 'temp-1',
      hasCodes: false,
    },
  ]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [createdProduct, setCreatedProduct] = useState<any>(null);
  const [generatingCodes, setGeneratingCodes] = useState(false);

  const handleProductChange = (field: keyof ProductFormData, value: any) => {
    setProductData(prev => ({ ...prev, [field]: value }));
  };

  const handleVariantChange = (index: number, field: keyof VariantFormData, value: any) => {
    const newVariants = [...variants];
    newVariants[index] = { ...newVariants[index], [field]: value };
    setVariants(newVariants);
  };

  const addVariant = () => {
    setVariants([
      ...variants,
      {
        name: `Variant ${variants.length + 1}`,
        base_price: '',
        sale_price: '',
        stock: '',
        attributes: {},
        images: [],
        imagePreviewUrls: [],
        imageUrls: [],
        tempId: `temp-${Date.now()}`,
        hasCodes: false,
      },
    ]);
  };

  const handleImageUpload = async (index: number, files: FileList | null) => {
    if (!files || files.length === 0) return;

    const newImages = Array.from(files);
    const newPreviewUrls = newImages.map(file => URL.createObjectURL(file));

    // Update preview immediately
    const newVariants = [...variants];
    newVariants[index] = {
      ...newVariants[index],
      images: [...newVariants[index].images, ...newImages],
      imagePreviewUrls: [...newVariants[index].imagePreviewUrls, ...newPreviewUrls],
    };
    setVariants(newVariants);

    // Upload to GitHub in background
    try {
      setUploadingImages(true);
      toast.loading('Uploading images to CDN...', { id: 'image-upload' });
      
      const category = productData.name || 'products';
      const uploadResults = await uploadMultipleFiles(newImages, category);
      
      // Update with CDN URLs
      const cdnUrls = uploadResults
        .filter(result => result.url && !result.error)
        .map(result => result.url as string);

      if (cdnUrls.length > 0) {
        const updatedVariants = [...variants];
        updatedVariants[index] = {
          ...updatedVariants[index],
          imageUrls: [...updatedVariants[index].imageUrls, ...cdnUrls],
        };
        setVariants(updatedVariants);
        toast.success(`${cdnUrls.length} image(s) uploaded successfully!`, { id: 'image-upload' });
      } else {
        toast.error('Failed to upload images', { id: 'image-upload' });
      }
    } catch (error) {
      console.error('Error uploading images:', error);
      toast.error('Failed to upload images to CDN', { id: 'image-upload' });
    } finally {
      setUploadingImages(false);
    }
  };

  const removeImage = (variantIndex: number, imageIndex: number) => {
    const newVariants = [...variants];
    const variant = newVariants[variantIndex];

    // Revoke the object URL to free memory
    URL.revokeObjectURL(variant.imagePreviewUrls[imageIndex]);

    variant.images = variant.images.filter((_, i) => i !== imageIndex);
    variant.imagePreviewUrls = variant.imagePreviewUrls.filter((_, i) => i !== imageIndex);
    variant.imageUrls = variant.imageUrls.filter((_, i) => i !== imageIndex);

    setVariants(newVariants);
  };

  const removeVariant = (index: number) => {
    if (variants.length > 1) {
      setVariants(variants.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!productData.name.trim()) {
      toast.error('Product name is required');
      return;
    }

    if (variants.some(v => !v.base_price)) {
      toast.error('All variants must have a base price');
      return;
    }

    if (uploadingImages) {
      toast.error('Please wait for images to finish uploading');
      return;
    }

    setLoading(true);
    try {
      // Format data for API with CDN URLs
      const formattedData = {
        ...productData,
        variants: variants.map(v => ({
          name: v.name,
          base_price: parseFloat(v.base_price),
          sale_price: v.sale_price ? parseFloat(v.sale_price) : null,
          stock: parseInt(v.stock) || 0,
          attributes: v.attributes,
          image_urls: v.imageUrls, // Send jsDelivr CDN URLs (SKU auto-generated by backend)
        })),
      };

      const response = await ProductsAPI.createProduct(formattedData);
      const product = response.data || response;
      setCreatedProduct(product);
      
      toast.success('Product created successfully!');
      
      // Generate codes for all variants
      if (product.variants && product.variants.length > 0) {
        setGeneratingCodes(true);
        toast.loading('Generating barcodes and QR codes...', { id: 'code-generation' });
        
        try {
          const codePromises = product.variants.map(async (variant: any) => {
            try {
              await ProductsAPI.generateVariantCodes(variant.id);
              return { success: true, variantId: variant.id };
            } catch (error) {
              console.error(`Failed to generate codes for variant ${variant.id}:`, error);
              return { success: false, variantId: variant.id };
            }
          });
          
          const results = await Promise.all(codePromises);
          const successCount = results.filter(r => r.success).length;
          
          if (successCount === product.variants.length) {
            toast.success('All barcodes and QR codes generated successfully!', { id: 'code-generation' });
          } else if (successCount > 0) {
            toast.success(`${successCount}/${product.variants.length} codes generated successfully`, { id: 'code-generation' });
          } else {
            toast.error('Failed to generate codes. You can generate them later from the product detail page.', { id: 'code-generation' });
          }
        } catch (error) {
          console.error('Error generating codes:', error);
          toast.error('Failed to generate codes. You can generate them later from the product detail page.', { id: 'code-generation' });
        } finally {
          setGeneratingCodes(false);
        }
      }
      
      // Navigate to product detail page to show the created product with codes
      navigate(`/admin/products/${product.id}`);
    } catch (error: any) {
      console.error('Error creating product:', error);
      toast.error(error?.message || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <button
        onClick={() => navigate('/admin/products')}
        className="flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 mb-6"
      >
        <ArrowLeftIcon size={20} className="mr-2" />
        Back to Products
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Add New Product</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Create a new product with variants. Barcodes and QR codes will be automatically generated.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Product Information */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Product Information
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Product Name *
              </label>
              <input
                type="text"
                value={productData.name}
                onChange={(e) => handleProductChange('name', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter product name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={productData.description}
                onChange={(e) => handleProductChange('description', e.target.value)}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter product description"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <div className="relative">
                <select
                  value={productData.category_id}
                  onChange={(e) => handleProductChange('category_id', e.target.value)}
                  disabled={loadingCategories}
                  className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white appearance-none disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {loadingCategories ? 'Loading categories...' : 'Select a category (optional)'}
                  </option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <ChevronDownIcon 
                  size={20} 
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none"
                />
              </div>
              {productData.category_id && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Selected: {categories.find(c => c.id === productData.category_id)?.name || 'Unknown'}
                </p>
              )}
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={productData.is_active}
                onChange={(e) => handleProductChange('is_active', e.target.checked)}
                className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
              />
              <label htmlFor="is_active" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Active (visible to customers)
              </label>
            </div>
          </div>
        </div>

        {/* Variants */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Product Variants
            </h2>
            <button
              type="button"
              onClick={addVariant}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              <PlusIcon size={18} />
              Add Variant
            </button>
          </div>

          <div className="space-y-4">
            {variants.map((variant, index) => (
              <div key={variant.tempId || index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    Variant {index + 1}
                  </h3>
                  {variants.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeVariant(index)}
                      className="text-red-600 hover:text-red-700 self-end sm:self-auto"
                    >
                      <XIcon size={20} />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Variant Details */}
                  <div className="lg:col-span-2 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Variant Name *
                      </label>
                      <input
                        type="text"
                        value={variant.name}
                        onChange={(e) => handleVariantChange(index, 'name', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="e.g., Small, Red, 500ml"
                        required
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        SKU will be auto-generated by the system
                      </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Base Price *
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={variant.base_price}
                          onChange={(e) => handleVariantChange(index, 'base_price', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="0.00"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Sale Price
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={variant.sale_price}
                          onChange={(e) => handleVariantChange(index, 'sale_price', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Stock Quantity
                        </label>
                        <input
                          type="number"
                          value={variant.stock}
                          onChange={(e) => handleVariantChange(index, 'stock', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="0"
                        />
                      </div>
                    </div>

                    {/* Image Upload Section */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Variant Images
                      </label>
                      
                      {/* Image Preview Grid */}
                      {variant.imagePreviewUrls.length > 0 && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                          {variant.imagePreviewUrls.map((url, imgIndex) => (
                            <div key={imgIndex} className="relative group">
                              <img
                                src={url}
                                alt={`Preview ${imgIndex + 1}`}
                                className="w-full h-24 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
                              />
                              <button
                                type="button"
                                onClick={() => removeImage(index, imgIndex)}
                                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <XIcon size={14} />
                              </button>
                              {imgIndex === 0 && (
                                <span className="absolute bottom-1 left-1 bg-primary text-white text-xs px-2 py-0.5 rounded">
                                  Primary
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Upload Button */}
                      <div className="flex items-center justify-center w-full">
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600">
                          <div className="flex flex-col items-center justify-center pt-5 pb-6">
                            <UploadIcon className="w-8 h-8 mb-2 text-gray-500 dark:text-gray-400" />
                            <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                              <span className="font-semibold">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              PNG, JPG, GIF up to 10MB
                            </p>
                          </div>
                          <input
                            type="file"
                            className="hidden"
                            accept="image/*"
                            multiple
                            onChange={(e) => handleImageUpload(index, e.target.files)}
                          />
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        First image will be set as primary. You can upload multiple images.
                      </p>
                    </div>
                  </div>

                  {/* Code Preview */}
                  <div className="lg:col-span-1">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                        Code Preview
                      </h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                        Barcodes and QR codes will be automatically generated after the product is created.
                      </p>
                      
                      {/* Preview placeholders */}
                      <div className="space-y-3">
                        <div className="text-center">
                          <div className="w-full h-12 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded flex items-center justify-center">
                            <span className="text-xs text-gray-400">Barcode Preview</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">Auto-generated SKU</p>
                        </div>
                        
                        <div className="text-center">
                          <div className="w-full h-12 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded flex items-center justify-center">
                            <span className="text-xs text-gray-400">QR Code Preview</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1 break-words">{variant.name}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/admin/products')}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || uploadingImages || generatingCodes}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadingImages ? 'Uploading Images...' : 
             generatingCodes ? 'Generating Codes...' :
             loading ? 'Creating...' : 'Create Product'}
          </button>
        </div>
      </form>
    </div>
  );
};
