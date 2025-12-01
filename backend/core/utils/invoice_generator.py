"""
Invoice PDF Generator using Jinja2 and WeasyPrint
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from pathlib import Path


class InvoiceGenerator:
    """Generate PDF invoices from HTML templates using Jinja2 and WeasyPrint"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the invoice generator
        
        Args:
            template_dir: Directory containing invoice templates
        """
        if template_dir is None:
            # Default to the templates directory
            base_dir = Path(__file__).parent
            template_dir = base_dir / "messages" / "templates" / "post_purchase"
        
        self.template_dir = Path(template_dir)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    def format_currency(self, amount: float, currency: str = "$") -> str:
        """Format amount as currency"""
        return f"{currency} {amount:,.2f}"
    
    def format_date(self, date_obj: datetime, format_str: str = "%B %d, %Y") -> str:
        """Format datetime object to string"""
        return date_obj.strftime(format_str)
    
    def generate_invoice_ref(self, order_id: str) -> str:
        """Generate invoice reference from order ID"""
        # Take first 8 characters of order ID and format
        short_id = order_id.replace("-", "")[:8].upper()
        return f"INV-{short_id}"
    
    def prepare_invoice_data(self, order_data: Dict) -> Dict:
        """
        Prepare invoice data from order information
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Dictionary with formatted invoice data
        """
        current_date = datetime.now()
        
        # Format items
        items = []
        for item in order_data.get('items', []):
            items.append({
                'name': item.get('product_name', 'Product'),
                'description': item.get('variant_name', ''),
                'unit_price': self.format_currency(item.get('price_per_unit', 0)),
                'quantity': item.get('quantity', 1),
                'total_price': self.format_currency(item.get('total_price', 0))
            })
        
        # Calculate discount percentage if applicable
        discount_percentage = 0
        if order_data.get('discount_amount', 0) > 0 and order_data.get('subtotal', 0) > 0:
            discount_percentage = round(
                (order_data['discount_amount'] / order_data['subtotal']) * 100
            )
        
        # Prepare invoice data
        invoice_data = {
            # Invoice metadata
            'bnw_invoice_ref': self.generate_invoice_ref(order_data.get('order_id', '')),
            'bnw_invoice_issue_date': self.format_date(current_date),
            'bnw_payment_due_date': self.format_date(current_date + timedelta(days=30)),
            'bnw_order_reference_id': order_data.get('order_id', ''),
            'bnw_order_placement_date': self.format_date(
                order_data.get('created_at', current_date)
            ),
            
            # Customer information
            'bnw_customer_full_name': order_data.get('customer_name', 'N/A'),
            'bnw_customer_email_address': order_data.get('customer_email', 'N/A'),
            'bnw_customer_phone_number': order_data.get('customer_phone', 'N/A'),
            
            # Financial data
            'bnw_order_subtotal_amount': self.format_currency(
                order_data.get('subtotal', 0)
            ),
            'bnw_tax_rate': order_data.get('tax_rate', 10),
            'bnw_tax_amount': self.format_currency(order_data.get('tax_amount', 0)),
            'bnw_discount_amount': self.format_currency(
                order_data.get('discount_amount', 0)
            ) if order_data.get('discount_amount', 0) > 0 else None,
            'discount_percentage': discount_percentage,
            'bnw_grand_total_amount': self.format_currency(
                order_data.get('total_amount', 0)
            ),
            
            # Items
            'items': items,
            
            # Company information
            'logo_url': order_data.get('logo_url', 'file://' + str(Path(__file__).parent.parent.parent.parent / 'frontend' / 'public' / 'banwe_logo_green.png')),
            'company_address_line1': order_data.get(
                'company_address_line1', 
                'Main Street, Number 66/B'
            ),
            'company_address_line2': order_data.get(
                'company_address_line2',
                'South Winbond, YK'
            ),
        }
        
        return invoice_data
    
    def generate_html(
        self, 
        order_data: Dict, 
        template_name: str = "invoice_template.html"
    ) -> str:
        """
        Generate HTML invoice from template
        
        Args:
            order_data: Order information dictionary
            template_name: Name of the Jinja2 template file
            
        Returns:
            Rendered HTML string
        """
        # Prepare data
        invoice_data = self.prepare_invoice_data(order_data)
        
        # Load and render template
        template = self.env.get_template(template_name)
        html_content = template.render(**invoice_data)
        
        return html_content
    
    def generate_pdf(
        self,
        order_data: Dict,
        output_path: str,
        template_name: str = "invoice_template.html"
    ) -> str:
        """
        Generate PDF invoice from template
        
        Args:
            order_data: Order information dictionary
            output_path: Path where PDF should be saved
            template_name: Name of the Jinja2 template file
            
        Returns:
            Path to generated PDF file
        """
        # Generate HTML
        html_content = self.generate_html(order_data, template_name)
        
        # Convert to PDF using WeasyPrint
        HTML(string=html_content).write_pdf(output_path)
        
        return output_path
    
    def generate_pdf_bytes(
        self,
        order_data: Dict,
        template_name: str = "invoice_template.html"
    ) -> bytes:
        """
        Generate PDF invoice as bytes (useful for email attachments)
        
        Args:
            order_data: Order information dictionary
            template_name: Name of the Jinja2 template file
            
        Returns:
            PDF content as bytes
        """
        # Generate HTML
        html_content = self.generate_html(order_data, template_name)
        
        # Convert to PDF bytes
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return pdf_bytes


# Example usage
if __name__ == "__main__":
    # Sample order data
    sample_order = {
        'order_id': 'a7b3c2d1-4e5f-6789-0abc-def123456789',
        'created_at': datetime.now(),
        'customer_name': 'Alisa Lumbert',
        'customer_email': 'alisa.lumbert@email.com',
        'customer_phone': '+1 (231) 321 4232',
        'subtotal': 210.00,
        'tax_rate': 10,
        'tax_amount': 21.00,
        'discount_amount': 11.55,
        'total_amount': 219.45,
        'items': [
            {
                'product_name': 'Items Name',
                'variant_name': 'Sample item product description',
                'price_per_unit': 20.00,
                'quantity': 3,
                'total_price': 60.00
            },
            {
                'product_name': 'Items Name',
                'variant_name': 'Another Sample item product description',
                'price_per_unit': 5.00,
                'quantity': 1,
                'total_price': 5.00
            },
            {
                'product_name': 'Items Name',
                'variant_name': 'Sample item product description',
                'price_per_unit': 40.00,
                'quantity': 2,
                'total_price': 80.00
            },
            {
                'product_name': 'Items Name',
                'variant_name': 'Another Sample item product description',
                'price_per_unit': 20.00,
                'quantity': 1,
                'total_price': 20.00
            },
            {
                'product_name': 'Items Name',
                'variant_name': 'Another Sample item product description',
                'price_per_unit': 15.00,
                'quantity': 3,
                'total_price': 45.00
            },
        ]
    }
    
    # Generate invoice
    generator = InvoiceGenerator()
    
    # Generate HTML (for preview)
    html = generator.generate_html(sample_order)
    print("HTML generated successfully")
    
    # Generate PDF
    output_file = "sample_invoice.pdf"
    generator.generate_pdf(sample_order, output_file)
    print(f"PDF generated: {output_file}")
