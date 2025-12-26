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
  role: 'customer' | 'admin' | 'supplier';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  profile_image?: string;
  date_of_birth?: string;
  gender?: string;
  language_preference?: string;
  currency_preference?: string;
}

// Product Types
export interface ProductImage {
  id: string;
  url: string;
  alt_text?: string;
  is_primary: boolean;
  display_order: number;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  name: string;
  base_price: number;
  sale_price?: number;
  stock: number;
  images: ProductImage[];
  product_name?: string;
  product_description?: string;
  attributes?: Record<string, any>;
  barcode?: string;  // Base64 encoded barcode image
  qr_code?: string;  // Base64 encoded QR code image
}

export interface Product {
  id: string;
  name: string;
  description: string;
  category_id?: string;
  brand_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  variants: ProductVariant[];
  images: ProductImage[];
  average_rating?: number;
  review_count?: number;
  category?: Category;
  brand?: Brand;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
  image_url?: string;
  is_active: boolean;
  display_order: number;
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
  variant: ProductVariant;
  quantity: number;
  price_per_unit: number;
  total_price: number;
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
  total_items: number;
  total_amount: number;
  created_at: string;
  updated_at?: string;
}

export interface AddToCartRequest {
  variant_id: string;
  quantity: number;
}

// Wishlist Types
export interface WishlistItem {
  id: string;
  product_id: string;
  product?: Product;
  variant_id?: string;
  variant?: ProductVariant;
  quantity: number;
  wishlist_id: string;
  added_at: string;
}

export interface Wishlist {
  id: string;
  user_id: string;
  name: string;
  is_default?: boolean;
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
}

export interface ShippingAddress {
  id?: string;
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
}

export interface Order {
  id: string;
  user_id: string;
  order_number: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  items: OrderItem[];
  subtotal: number;
  tax: number;
  shipping_cost: number;
  total_amount: number;
  shipping_address: ShippingAddress;
  payment_method?: string;
  payment_status: 'pending' | 'completed' | 'failed' | 'refunded';
  tracking_number?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

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

// Notification Types
export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'order' | 'payment' | 'shipping';
  is_read: boolean;
  link?: string;
  created_at: string;
  timestamp?: string;
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
  amount: number;
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
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

// System Settings Types
export interface SystemSetting {
  id: string;
  key: string;
  value: string;
  value_type: 'string' | 'integer' | 'float' | 'boolean' | 'uuid';
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface SystemSettingUpdate {
  value?: string;
  value_type?: 'string' | 'integer' | 'float' | 'boolean' | 'uuid';
  description?: string;
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
  postal_code: string;
  country: string;
  phone?: string;
  is_default?: boolean;
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
  addToCart: (variantId: string, quantity: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
}

export interface WishlistContextType {
  wishlists: Wishlist[];
  isLoading: boolean;
  addToWishlist: (productId: string, wishlistId?: string) => Promise<void>;
  removeFromWishlist: (itemId: string) => Promise<void>;
  refreshWishlists: () => Promise<void>;
}

export interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  refreshNotifications: () => Promise<void>;
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