-- Add missing fields to cart table
ALTER TABLE carts 
ADD COLUMN IF NOT EXISTS promocode_id UUID REFERENCES promocodes(id),
ADD COLUMN IF NOT EXISTS discount_amount FLOAT DEFAULT 0.0;

-- Add missing fields to cart_items table  
ALTER TABLE cart_items
ADD COLUMN IF NOT EXISTS total_price FLOAT NOT NULL DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS saved_for_later BOOLEAN DEFAULT FALSE;

-- Update existing cart_items to calculate total_price
UPDATE cart_items 
SET total_price = price_per_unit * quantity 
WHERE total_price = 0.0;