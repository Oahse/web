# Screenshot Capture Guide

This guide provides step-by-step instructions for capturing professional screenshots and GIFs for the Banwee E-commerce Platform documentation.

## Prerequisites

### Tools Needed

#### For Screenshots
- **macOS**: Built-in Screenshot tool (Cmd + Shift + 4)
- **Windows**: Snipping Tool or Snip & Sketch (Windows + Shift + S)
- **Linux**: GNOME Screenshot or Flameshot
- **Browser**: Chrome/Firefox DevTools for responsive views

#### For GIFs
- **macOS**: [Kap](https://getkap.co/) (free, open-source)
- **Windows**: [ScreenToGif](https://www.screentogif.com/) (free)
- **Cross-platform**: [LICEcap](https://www.cockos.com/licecap/) (free)

#### For Editing
- **Image Optimization**: [TinyPNG](https://tinypng.com/), [ImageOptim](https://imageoptim.com/)
- **Annotations**: [Skitch](https://evernote.com/products/skitch), [Annotate](https://annotate.app/)
- **GIF Optimization**: [Gifski](https://gif.ski/), [ezgif.com](https://ezgif.com/)

## Screenshot Specifications

### Dimensions

| Device Type | Resolution | Use Case |
|-------------|-----------|----------|
| Desktop (Primary) | 1920x1080 | Main documentation screenshots |
| Desktop (Alt) | 1440x900 | Alternative desktop view |
| Tablet | 768x1024 | iPad/tablet responsive view |
| Mobile | 375x812 | iPhone X/modern mobile view |

### Format & Quality

- **Format**: PNG (for screenshots), GIF (for animations)
- **Color Depth**: 24-bit color
- **Compression**: Optimize to < 500KB per image
- **Background**: Use actual application, not mockups

## Preparation Steps

### 1. Set Up Test Environment

```bash
# Start the application
./docker-start.sh

# Seed with sample data
./seed-database.sh

# Access the application
# Frontend: http://localhost:5173
# Admin: http://localhost:5173/admin
```

### 2. Prepare Sample Data

Ensure the database has:
- ✅ At least 20 diverse products across multiple categories
- ✅ Sample orders in various states (pending, shipped, delivered)
- ✅ Multiple user accounts (customer, supplier, admin)
- ✅ Product reviews and ratings
- ✅ Realistic product images (not placeholders)

### 3. Browser Setup

1. **Clear browser cache** to ensure fresh load
2. **Set browser zoom to 100%**
3. **Use Chrome DevTools** for responsive views:
   - Press F12
   - Click device toolbar icon (Cmd/Ctrl + Shift + M)
   - Select device or custom dimensions

### 4. Clean Up UI

Before capturing:
- ✅ Close any development tools
- ✅ Hide browser bookmarks bar
- ✅ Clear any error messages or notifications
- ✅ Ensure proper lighting/theme (use light mode for consistency)
- ✅ Use realistic user data (no "test@test.com")

## Screenshot Checklist

### Customer Experience Screenshots

#### 1. Homepage (`homepage.png`)
- **URL**: http://localhost:5173
- **Resolution**: 1920x1080
- **Content**:
  - Hero section with banner
  - Featured products grid
  - Category navigation
  - Footer visible
- **Notes**: Scroll to show full page or capture in sections

#### 2. Product Listing (`product-listing.png`)
- **URL**: http://localhost:5173/products
- **Resolution**: 1920x1080
- **Content**:
  - Product grid with images
  - Filters sidebar (categories, price range)
  - Sort dropdown
  - Pagination
- **Notes**: Show at least 8-12 products

#### 3. Product Details (`product-details.png`)
- **URL**: http://localhost:5173/products/[product-id]
- **Resolution**: 1920x1080
- **Content**:
  - Product image gallery
  - Product information (name, price, description)
  - Add to cart button
  - Product reviews section
  - Related products
- **Notes**: Choose a product with multiple images and reviews

#### 4. Shopping Cart (`cart.png`)
- **URL**: http://localhost:5173/cart
- **Resolution**: 1920x1080
- **Content**:
  - Cart items with images
  - Quantity controls
  - Price breakdown (subtotal, tax, shipping)
  - Checkout button
- **Notes**: Have 3-5 items in cart

#### 5. Checkout (`checkout.png`)
- **URL**: http://localhost:5173/checkout
- **Resolution**: 1920x1080
- **Content**:
  - Shipping address form
  - Payment method selection
  - Order summary
  - Stripe payment form
- **Notes**: Use test Stripe card (4242 4242 4242 4242)

### Admin Dashboard Screenshots

#### 6. Analytics Dashboard (`admin-dashboard.png`)
- **URL**: http://localhost:5173/admin
- **Resolution**: 1920x1080
- **Content**:
  - Sales charts (line/bar graphs)
  - Key metrics cards (revenue, orders, users)
  - Recent activity feed
  - Top products table
- **Notes**: Ensure charts have data

#### 7. Product Management (`admin-products.png`)
- **URL**: http://localhost:5173/admin/products
- **Resolution**: 1920x1080
- **Content**:
  - Products table with images
  - Search and filter controls
  - Add product button
  - Edit/delete actions
- **Notes**: Show at least 10 products

#### 8. Order Management (`admin-orders.png`)
- **URL**: http://localhost:5173/admin/orders
- **Resolution**: 1920x1080
- **Content**:
  - Orders table with status badges
  - Filter by status
  - Order details modal or page
  - Status update controls
- **Notes**: Show orders in different states

#### 9. User Management (`admin-users.png`)
- **URL**: http://localhost:5173/admin/users
- **Resolution**: 1920x1080
- **Content**:
  - Users table with roles
  - Role filter dropdown
  - User actions (edit, deactivate)
  - Order count column
- **Notes**: Show mix of customers, suppliers, admins

## GIF Workflow Demonstrations

### 1. Customer Journey (`customer-journey.gif`)

**Duration**: 15-20 seconds  
**Steps**:
1. Start on homepage
2. Click on a product category
3. Click on a product
4. Click "Add to Cart"
5. Navigate to cart
6. Click "Checkout"
7. Show checkout form

**Settings**:
- Frame rate: 15 FPS
- Size: 1280x720 (to keep file size manageable)
- Max file size: 5MB

### 2. Admin Product Creation (`admin-product-create.gif`)

**Duration**: 20-25 seconds  
**Steps**:
1. Navigate to admin products page
2. Click "Add Product"
3. Fill in product details (name, price, description)
4. Upload product image
5. Select category
6. Click "Save"
7. Show success message and new product in list

**Settings**:
- Frame rate: 15 FPS
- Size: 1280x720
- Max file size: 5MB

### 3. Order Management (`admin-order-management.gif`)

**Duration**: 15-20 seconds  
**Steps**:
1. Navigate to admin orders page
2. Click on an order
3. View order details
4. Update order status to "Shipped"
5. Add tracking number
6. Show success notification

**Settings**:
- Frame rate: 15 FPS
- Size: 1280x720
- Max file size: 5MB

## Capture Process

### For Screenshots

#### macOS
```bash
# Full screen
Cmd + Shift + 3

# Selected area (recommended)
Cmd + Shift + 4
# Then drag to select area

# Window
Cmd + Shift + 4, then press Space, then click window
```

#### Windows
```bash
# Snipping Tool
Windows + Shift + S
# Then select area

# Or use Snip & Sketch
Windows + Shift + S
```

#### Browser DevTools (Responsive)
1. Open DevTools (F12)
2. Click device toolbar (Cmd/Ctrl + Shift + M)
3. Select device or enter custom dimensions
4. Click "..." menu → "Capture screenshot"

### For GIFs

#### Using Kap (macOS)
1. Open Kap
2. Adjust recording area
3. Click record button
4. Perform actions
5. Click stop
6. Export as GIF
7. Optimize with Gifski if needed

#### Using ScreenToGif (Windows)
1. Open ScreenToGif
2. Click "Recorder"
3. Adjust recording area
4. Click record
5. Perform actions
6. Click stop
7. Edit if needed
8. Export as GIF

## Post-Processing

### Image Optimization

1. **Resize if needed**
   ```bash
   # Using ImageMagick
   convert input.png -resize 1920x1080 output.png
   ```

2. **Compress**
   - Upload to [TinyPNG](https://tinypng.com/)
   - Or use ImageOptim (macOS)
   - Target: < 500KB per image

3. **Rename**
   - Use exact filenames from docs/screenshots/README.md
   - Use lowercase with hyphens
   - Example: `admin-dashboard.png`

### GIF Optimization

1. **Reduce colors**
   ```bash
   # Using gifsicle
   gifsicle -O3 --colors 128 input.gif -o output.gif
   ```

2. **Reduce frame rate**
   - Use 10-15 FPS (not 30 FPS)
   - Remove duplicate frames

3. **Compress**
   - Use [ezgif.com](https://ezgif.com/optimize)
   - Target: < 5MB per GIF

## File Organization

Save files to:
```
docs/screenshots/
├── homepage.png
├── product-listing.png
├── product-details.png
├── cart.png
├── checkout.png
├── admin-dashboard.png
├── admin-products.png
├── admin-orders.png
├── admin-users.png
├── customer-journey.gif
├── admin-product-create.gif
└── admin-order-management.gif
```

## Quality Checklist

Before committing screenshots:

- [ ] Correct dimensions (1920x1080 for desktop)
- [ ] File size < 500KB (images) or < 5MB (GIFs)
- [ ] PNG format for screenshots, GIF for animations
- [ ] Realistic sample data (no "test" or placeholder text)
- [ ] Clean UI (no error messages or dev tools)
- [ ] Proper lighting/contrast
- [ ] Correct filename
- [ ] Optimized for web

## Updating README

After adding screenshots, verify they display correctly:

```bash
# View README locally
# Use a Markdown viewer or push to GitHub to see rendered version
```

The README already has the correct image paths:
```markdown
![Homepage](docs/screenshots/homepage.png)
```

## Tips for Professional Screenshots

1. **Consistency**: Use the same browser, zoom level, and theme for all screenshots
2. **Timing**: Capture when UI is fully loaded (no loading spinners)
3. **Content**: Use realistic, diverse data that showcases features
4. **Focus**: Highlight the feature being demonstrated
5. **Context**: Include enough UI to show where the feature is located
6. **Quality**: Use high-resolution displays (Retina/4K) for crisp images
7. **Annotations**: Add arrows or highlights if needed to draw attention

## Troubleshooting

### Issue: Screenshots are blurry
- **Solution**: Ensure browser zoom is at 100%, use high-DPI display

### Issue: File size too large
- **Solution**: Use TinyPNG or ImageOptim to compress

### Issue: GIF is choppy
- **Solution**: Reduce frame rate to 10-15 FPS, remove duplicate frames

### Issue: Colors look different
- **Solution**: Use sRGB color profile, disable color management in browser

## Need Help?

If you encounter issues:
1. Check this guide thoroughly
2. Review existing screenshots in similar projects
3. Ask in GitHub Discussions
4. Contact maintainers

---

**Ready to capture?** Follow this guide step-by-step and you'll have professional documentation screenshots in no time! 📸
