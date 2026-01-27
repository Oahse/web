// Common Types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// User Types
export interface User {
  id: string;
  email: string;
  firstname: string;
  lastname: string;
  full_name?: string;
  phone?: string;
  phone_verified?: boolean;
  role: 'guest' | 'admin' | 'manager' | 'support' | 'customer' | 'supplier';
  account_status?: string;
  verification_status?: string;
  verified: boolean;
  is_active: boolean;
  avatar_url?: string;
  country?: string;
  language?: string;
  timezone?: string;
  last_login?: string;
  last_activity_at?: string;
  login_count?: number;
  failed_login_attempts?: number;
  locked_until?: string;
  stripe_customer_id?: string;
  preferences?: Record<string, any>;
  age?: string;
  gender?: string;
  created_at: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  is_verified?: boolean;
  profile_image?: string;
  date_of_birth?: string;
  language_preference?: string;
  currency_preference?: string;
}

// Product Types
export interface ProductImage {
  id: string;
  variant_id: string;
  url: string;
  alt_text?: string;
  is_primary: boolean;
  sort_order: number;
  format?: string;
  created_at?: string;
  // Legacy field for backward compatibility
  display_order?: number;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  name: string;
  base_price: number;
  sale_price?: number | null;
  current_price?: number;
  discount_percentage?: number;
  stock?: number;
  attributes?: Record<string, any>;
  is_active: boolean;
  barcode?: string;
  qr_code?: string;
  images: ProductImage[];
  primary_image?: ProductImage;
  image_count?: number;
  created_at: string;
  updated_at?: string;
  // Enhanced product information for cart items
  product_name?: string;
  product_description?: string;
  product_short_description?: string;
  product_slug?: string;
  product_category_id?: string;
  product_rating_average?: number;
  product_rating_count?: number;
  product_is_featured?: boolean;
  product_specifications?: Record<string, any>;
  product_dietary_tags?: string[];
  product_tags?: string[];
  product_origin?: string;
  // Enhanced inventory information
  inventory_quantity_available?: number;
  inventory_reorder_level?: number;
  inventory_last_updated?: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  image_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  slug?: string;
  parent_id?: string;
  display_order?: number;
}

export interface Product {
  id: string;
  name: string;
  slug?: string;
  description?: string;
  short_description?: string;
  category_id?: string;
  supplier_id?: string;
  product_status?: string;
  availability_status?: string;
  min_price?: number;
  max_price?: number;
  rating_average?: number;
  rating_count?: number;
  review_count?: number;
  is_featured?: boolean;
  is_bestseller?: boolean;
  specifications?: Record<string, any>;
  dietary_tags?: Record<string, any>;
  tags?: string[];
  keywords?: string[];
  published_at?: string;
  view_count?: number;
  purchase_count?: number;
  origin?: string;
  price_range?: { min: number; max: number };
  in_stock?: boolean;
  variants: ProductVariant[];
  images?: ProductImage[];
  category?: Category;
  supplier?: User;
  created_at: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  brand_id?: string;
  brand?: Brand;
  is_active?: boolean;
  average_rating?: number;
  price?: number;
  discountPrice?: number | null;
  featured?: boolean;
  rating?: number;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
}

// Cart Types
export interface CartItem {
  id: string;
  cart_id: string;
  variant_id: string;
  variant: ProductVariant;
  quantity: number;
  price_per_unit: number;
  total_price: number;
  saved_for_later?: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Cart {
  id: string;
  user_id: string;
  promocode_id?: string;
  discount_amount?: number;
  items: CartItem[];
  created_at: string;
  updated_at?: string;
  // Computed properties from backend
  subtotal?: number;
  tax_amount?: number;
  shipping_amount?: number;
  total_amount?: number;
  item_count?: number;
  currency?: string;
  // Legacy fields for backward compatibility
  total_items?: number;
}

export interface AddToCartRequest {
  variant_id: string;
  quantity: number;
}

// Wishlist Types
export interface WishlistItem {
  id: string;
  wishlist_id: string;
  product_id: string;
  variant_id?: string;
  quantity: number;
  product?: Product;
  variant?: ProductVariant;
  created_at: string;
  // Computed property
  added_at?: string;
}

export interface Wishlist {
  id: string;
  user_id: string;
  name: string;
  is_default?: boolean;
  is_public?: boolean;
  items: WishlistItem[];
  created_at: string;
  updated_at?: string;
}

// Order Types
export interface OrderItem {
  id: string;
  order_id: string;
  variant_id: string;
  variant: ProductVariant;
  quantity: number;
  price_per_unit: number;
  total_price: number;
  created_at: string;
}

export interface Address {
  id?: string;
  user_id?: string;
  street: string;
  city: string;
  state: string;
  country: string;
  post_code: string;
  kind?: string;
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  postal_code?: string;
  phone?: string;
}

export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  guest_email?: string;
  order_status: string;
  payment_status: string;
  fulfillment_status: string;
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  shipping_method?: string;
  tracking_number?: string;
  carrier?: string;
  billing_address: Record<string, any>;
  shipping_address: Record<string, any>;
  confirmed_at?: string;
  shipped_at?: string;
  delivered_at?: string;
  cancelled_at?: string;
  customer_notes?: string;
  internal_notes?: string;
  source: string;
  items: OrderItem[];
  created_at: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  status?: string;
  tax?: number;
  shipping_cost?: number;
  payment_method?: string;
  notes?: string;
}

// Legacy type for backward compatibility
export interface ShippingAddress extends Address {}

// Review Types
export interface Review {
  id: string;
  product_id: string;
  user_id: string;
  user?: User;
  rating: number;
  title?: string;
  comment?: string;
  is_verified_purchase: boolean;
  helpful_count: number;
  created_at: string;
  updated_at?: string;
}

// Payment Types
export interface PaymentMethod {
  id: string;
  user_id: string;
  type: 'card' | 'paypal' | 'bank_transfer';
  last_four?: string;
  brand?: string;
  expiry_month?: number;
  expiry_year?: number;
  is_default: boolean;
}

export interface PaymentIntent {
  id: string;
  amount: number;
  currency: string;
  status: string;
  client_secret?: string;
}

// Subscription Types
export interface Subscription {
  id: string;
  user_id: string;
  plan_id: string;
  status: 'active' | 'cancelled' | 'expired' | 'paused';
  start_date: string;
  end_date?: string;
  next_billing_date?: string;
  amount?: number;
  price?: number;
  billing_cycle: 'weekly' | 'monthly' | 'yearly';
  currency?: string;
  delivery_type?: string;
  auto_renew?: boolean;
  tax_rate?: number;
  shipping_cost?: number;
  products?: Array<{
    id: string;
    name: string;
    price: number;
    image?: string;
    quantity?: number;
    currency?: string;
  }>;
  created_at?: string;
  updated_at?: string;
}

// Admin Types
export interface DashboardStats {
  total_revenue: number;
  total_orders: number;
  total_users: number;
  total_products: number;
  recent_orders: Order[];
  revenue_trend?: Array<{ date: string; amount: number }>;
}

// Filter Types
export interface ProductFilters {
  search?: string;
  category_id?: string;
  brand_id?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  in_stock?: boolean;
  sort_by?: 'price_asc' | 'price_desc' | 'name_asc' | 'name_desc' | 'date_desc' | 'rating_desc';
  page?: number;
  per_page?: number;
}

// Form Types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  firstname: string;
  lastname: string;
  phone?: string;
}

export interface AddressFormData {
  street: string;
  city: string;
  state: string;
  post_code: string;
  country: string;
  phone?: string;
  is_default?: boolean;
  // Legacy field for backward compatibility
  postal_code?: string;
}

// Context Types
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterFormData) => Promise<void>;
  logout: () => void;
  updateUser: (data: Partial<User>) => Promise<void>;
}

export interface CartContextType {
  cart: Cart | null;
  isLoading: boolean;
  loading?: boolean;
  addItem: (request: AddToCartRequest) => Promise<void>;
  addToCart?: (variantId: string, quantity: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  removeFromCart?: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
}

export interface WishlistContextType {
  wishlists: Wishlist[];
  defaultWishlist?: Wishlist | null;
  isLoading: boolean;
  addItem: (productId: string, variantId?: string, quantity?: number) => Promise<void>;
  addToWishlist?: (productId: string, wishlistId?: string) => Promise<void>;
  removeItem: (wishlistId: string, itemId: string) => Promise<void>;
  removeFromWishlist?: (itemId: string) => Promise<void>;
  isInWishlist: (productId: string, variantId?: string) => boolean;
  refreshWishlists: () => Promise<void>;
}

export interface ThemeContextType {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  isDark: boolean;
}

// Component Props Types
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Array<{ value: string; label: string }>;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Utility Types
export type SortOrder = 'asc' | 'desc';
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// Barcode/QR Code Types
export interface BarcodeData {
  variant_id: string;
  barcode?: string;
  qr_code?: string;
}

export interface BarcodeUpdateRequest {
  barcode?: string;
  qr_code?: string;
}

// Activity Log Types
export interface ActivityLog {
  id: string;
  user_id?: string;
  action_type: string;
  description: string;
  metadata?: Record<string, any>;
  created_at: string;
}

// Inventory Types
export interface WarehouseLocation {
  id: string;
  name: string;
  address?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface WarehouseLocationResponse extends WarehouseLocation {
  data?: WarehouseLocation[];
}

export interface WarehouseLocationCreate {
  name: string;
  address?: string;
  description?: string;
}

export interface WarehouseLocationUpdate {
  name?: string;
  address?: string;
  description?: string;
}

export interface InventoryItem {
  id: string;
  variant_id: string;
  location_id: string;
  quantity: number;
  quantity_available: number;
  low_stock_threshold: number;
  reorder_point: number;
  inventory_status: string;
  last_restocked_at?: string;
  last_sold_at?: string;
  version: number;
  variant?: ProductVariant;
  location?: WarehouseLocation;
  created_at: string;
  updated_at?: string;
}

export interface InventoryResponse extends InventoryItem {}

export interface InventoryCreate {
  variant_id: string;
  location_id: string;
  quantity: number;
  quantity_available?: number;
  low_stock_threshold?: number;
  reorder_point?: number;
  inventory_status?: string;
}

export interface InventoryUpdate {
  location_id?: string;
  quantity?: number;
  quantity_available?: number;
  low_stock_threshold?: number;
  reorder_point?: number;
  inventory_status?: string;
}

export interface StockAdjustment {
  id: string;
  inventory_id: string;
  variant_id: string;
  quantity_change: number;
  reason: string;
  notes?: string;
  adjusted_by_user_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface StockAdjustmentCreate {
  variant_id: string;
  location_id?: string;
  quantity_change: number;
  reason: string;
  notes?: string;
  product_id?: string; // For form selection
}

export interface StockAdjustmentResponse extends StockAdjustment {}

export interface InventoryAdjustment {
  id: string;
  inventory_item_id: string;
  adjustment_type: 'increase' | 'decrease' | 'set';
  quantity_change: number;
  new_quantity: number;
  reason?: string;
  notes?: string;
  created_by?: string;
  created_at: string;
}
