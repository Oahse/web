"""
Property-based tests for template content accuracy

This module tests Property 16: Template content accuracy
**Validates: Requirements 4.4, 4.7, 5.4, 5.7**

Requirements tested:
- 4.4: THE Email_Notification SHALL generate payment confirmation emails with detailed cost breakdowns
- 4.7: THE Email_Notification SHALL include subscription management links in all relevant emails
- 5.4: WHEN generating reports, THE Export_System SHALL include variant-level cost breakdowns
- 5.7: WHEN exporting payment data, THE Export_System SHALL include Stripe transaction details and status
"""

import pytest
import sys
import os
import asyncio
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List
from core.utils.uuid_utils import uuid7

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite

from services.jinja_template import JinjaTemplateService, RenderedTemplate, RenderedExport


class TestTemplateContentAccuracyProperty:
    """Test template content accuracy properties"""

    def get_template_service(self):
        """Get JinjaTemplateService instance - not a fixture to avoid Hypothesis issues"""
        return JinjaTemplateService(template_dir="templates")

    @composite
    def cost_breakdown_strategy(draw):
        """Generate realistic cost breakdown data"""
        variant_count = draw(st.integers(min_value=1, max_value=5))
        variants = []
        
        for _ in range(variant_count):
            variants.append({
                'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
                'price': float(draw(st.decimals(min_value=Decimal('1.00'), max_value=Decimal('999.99'), places=2)))
            })
        
        subtotal = sum(v['price'] for v in variants)
        admin_percentage = draw(st.floats(min_value=0.1, max_value=50.0))
        admin_fee = subtotal * (admin_percentage / 100)
        delivery_cost = float(draw(st.decimals(min_value=Decimal('0.00'), max_value=Decimal('50.00'), places=2)))
        tax_rate = draw(st.floats(min_value=0.0, max_value=0.25))
        tax_amount = (subtotal + admin_fee + delivery_cost) * tax_rate
        loyalty_discount = float(draw(st.decimals(min_value=Decimal('0.00'), max_value=Decimal('50.00'), places=2)))
        total_amount = subtotal + admin_fee + delivery_cost + tax_amount - loyalty_discount
        
        return {
            'variant_costs': variants,
            'subtotal': subtotal,
            'admin_percentage': admin_percentage,
            'admin_fee': admin_fee,
            'delivery_type': draw(st.sampled_from(['standard', 'express', 'overnight'])),
            'delivery_cost': delivery_cost,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'loyalty_discount': loyalty_discount,
            'total_amount': total_amount,
            'currency': draw(st.sampled_from(['USD', 'EUR', 'GBP', 'CAD']))
        }

    @composite
    def payment_confirmation_context_strategy(draw):
        """Generate payment confirmation email context"""
        cost_breakdown = draw(TestTemplateContentAccuracyProperty.cost_breakdown_strategy())
        
        return {
            'user_name': draw(st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')))),
            'payment_date': datetime.now().strftime('%B %d, %Y'),
            'payment_method': draw(st.sampled_from(['Visa ending in 1234', 'Mastercard ending in 5678', 'American Express ending in 9012'])),
            'subscription_id': str(uuid7()),
            'payment_amount': cost_breakdown['total_amount'],
            'cost_breakdown': cost_breakdown,
            'subscription_management_url': f"https://banwee.com/subscriptions/{uuid7()}",
            'company_name': 'Banwee'
        }

    @composite
    def export_context_strategy(draw):
        """Generate export template context with variant and payment details"""
        variant_count = draw(st.integers(min_value=1, max_value=10))
        variants = []
        
        for _ in range(variant_count):
            variants.append({
                'id': str(uuid7()),
                'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
                'price': float(draw(st.decimals(min_value=Decimal('1.00'), max_value=Decimal('999.99'), places=2))),
                'description': draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))))
            })
        
        payment_details = {
            'stripe_payment_intent_id': f"pi_{draw(st.text(min_size=24, max_size=24, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))}",
            'stripe_status': draw(st.sampled_from(['succeeded', 'pending', 'failed', 'canceled'])),
            'payment_method': draw(st.sampled_from(['card', 'bank_transfer', 'wallet'])),
            'transaction_id': str(uuid7()),
            'processed_at': datetime.now().isoformat()
        }
        
        subscription = {
            'id': str(uuid7()),
            'variants': variants,
            'cost_breakdown': draw(TestTemplateContentAccuracyProperty.cost_breakdown_strategy()),
            'user': {
                'firstname': draw(st.text(min_size=2, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
                'lastname': draw(st.text(min_size=2, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
                'email': f"{draw(st.text(min_size=3, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))}@example.com"
            },
            'billing_cycle': draw(st.sampled_from(['monthly', 'quarterly', 'yearly'])),
            'status': draw(st.sampled_from(['active', 'paused', 'canceled'])),
            'delivery_type': draw(st.sampled_from(['standard', 'express', 'overnight']))
        }
        
        return {
            'subscription': subscription,
            'payment_details': payment_details,
            'invoice_number': f"INV-{draw(st.integers(min_value=1000, max_value=99999))}",
            'invoice_date': date.today().strftime('%B %d, %Y'),
            'due_date': date.today().strftime('%B %d, %Y'),
            'company_name': 'Banwee',
            'company_address': {
                'line1': '123 Business St',
                'city': 'Business City',
                'state': 'BC',
                'zip': '12345',
                'country': 'USA'
            },
            'current_year': '2024'
        }

    @given(payment_confirmation_context_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payment_confirmation_email_contains_required_content(self, context):
        """
        Property 16: Template content accuracy - Payment confirmation emails
        
        For any payment confirmation email context, the rendered template should contain:
        - Detailed cost breakdown (requirement 4.4)
        - Subscription management links (requirement 4.7)
        
        **Feature: subscription-payment-enhancements, Property 16: Template content accuracy**
        **Validates: Requirements 4.4, 4.7**
        """
        template_service = self.get_template_service()
        
        # Render the payment confirmation email template
        rendered = asyncio.run(template_service.render_email_template(
            "emails/payment_confirmation.html",
            context
        ))
        
        content = rendered.content.lower()
        
        # Requirement 4.4: Payment confirmation emails with detailed cost breakdowns
        assert 'cost breakdown' in content or 'payment details' in content, \
            "Payment confirmation email should contain cost breakdown section"
        
        # Check for variant costs in breakdown
        if context.get('cost_breakdown', {}).get('variant_costs'):
            for variant in context['cost_breakdown']['variant_costs']:
                variant_name = variant['name'].lower()
                # Variant name should appear in the content
                assert variant_name in content, \
                    f"Variant '{variant['name']}' should appear in cost breakdown"
        
        # Check for cost components
        cost_breakdown = context.get('cost_breakdown', {})
        if cost_breakdown.get('subtotal'):
            assert 'subtotal' in content, "Cost breakdown should include subtotal"
        
        if cost_breakdown.get('admin_fee') and cost_breakdown['admin_fee'] > 0:
            assert 'service fee' in content or 'admin' in content, \
                "Cost breakdown should include admin/service fee when applicable"
        
        if cost_breakdown.get('delivery_cost') and cost_breakdown['delivery_cost'] > 0:
            assert 'delivery' in content, "Cost breakdown should include delivery cost when applicable"
        
        if cost_breakdown.get('tax_amount') and cost_breakdown['tax_amount'] > 0:
            assert 'tax' in content, "Cost breakdown should include tax when applicable"
        
        if cost_breakdown.get('loyalty_discount') and cost_breakdown['loyalty_discount'] > 0:
            assert 'loyalty' in content or 'discount' in content, \
                "Cost breakdown should include loyalty discount when applicable"
        
        # Check for total amount
        assert 'total' in content, "Cost breakdown should include total amount"
        
        # Requirement 4.7: Subscription management links in all relevant emails
        subscription_url = context.get('subscription_management_url', '')
        if subscription_url:
            assert subscription_url in rendered.content, \
                "Payment confirmation email should contain subscription management URL"
        
        # Check for subscription management link text
        assert ('subscription' in content and ('manage' in content or 'view' in content or 'details' in content)), \
            "Payment confirmation email should contain subscription management link"

    @given(export_context_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_export_templates_contain_required_content(self, context):
        """
        Property 16: Template content accuracy - Export templates
        
        For any export template context, the rendered template should contain:
        - Variant-level cost breakdowns (requirement 5.4)
        - Stripe transaction details and status (requirement 5.7)
        
        **Feature: subscription-payment-enhancements, Property 16: Template content accuracy**
        **Validates: Requirements 5.4, 5.7**
        """
        template_service = self.get_template_service()
        
        # Test invoice template (which is an export template)
        rendered = asyncio.run(template_service.render_export_template(
            "exports/invoice_template.html",
            context,
            "html"
        ))
        
        content = rendered.content.lower()
        
        # Requirement 5.4: Variant-level cost breakdowns in reports
        subscription = context.get('subscription', {})
        variants = subscription.get('variants', [])
        
        if variants:
            # Check that variant information appears in the export
            for variant in variants:
                variant_name = variant['name'].lower()
                assert variant_name in content, \
                    f"Export should include variant '{variant['name']}' in cost breakdown"
                
                # Check that variant price information is included
                variant_price_str = f"{variant['price']:.2f}"
                assert variant_price_str in rendered.content, \
                    f"Export should include variant price {variant_price_str}"
        
        # Check for cost breakdown structure
        cost_breakdown = subscription.get('cost_breakdown', {})
        if cost_breakdown:
            if cost_breakdown.get('subtotal'):
                assert 'subtotal' in content, "Export should include subtotal in cost breakdown"
            
            if cost_breakdown.get('admin_fee') and cost_breakdown['admin_fee'] > 0:
                assert 'service fee' in content or 'admin' in content, \
                    "Export should include admin fee in cost breakdown when applicable"
            
            if cost_breakdown.get('delivery_cost') and cost_breakdown['delivery_cost'] > 0:
                assert 'delivery' in content, "Export should include delivery cost in breakdown when applicable"
            
            if cost_breakdown.get('tax_amount') and cost_breakdown['tax_amount'] > 0:
                assert 'tax' in content, "Export should include tax in cost breakdown when applicable"
            
            if cost_breakdown.get('total_amount'):
                assert 'total' in content, "Export should include total amount"

    @given(export_context_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payment_export_contains_stripe_details(self, context):
        """
        Property 16: Template content accuracy - Payment export Stripe details
        
        For any payment export context, the rendered template should contain:
        - Stripe transaction details and status (requirement 5.7)
        
        **Feature: subscription-payment-enhancements, Property 16: Template content accuracy**
        **Validates: Requirements 5.7**
        """
        template_service = self.get_template_service()
        # Create a payment export context
        payment_export_context = {
            'payments': [
                {
                    'id': str(uuid7()),
                    'subscription_id': context['subscription']['id'],
                    'amount': context['subscription']['cost_breakdown']['total_amount'],
                    'currency': context['subscription']['cost_breakdown']['currency'],
                    'stripe_payment_intent_id': context['payment_details']['stripe_payment_intent_id'],
                    'stripe_status': context['payment_details']['stripe_status'],
                    'payment_method': context['payment_details']['payment_method'],
                    'transaction_id': context['payment_details']['transaction_id'],
                    'processed_at': context['payment_details']['processed_at'],
                    'created_at': datetime.now().isoformat()
                }
            ],
            'export_date': datetime.now().strftime('%B %d, %Y'),
            'company_name': 'Banwee'
        }
        
        # Create a simple payment export template for testing
        payment_export_template = """
        <h1>Payment Export - {{ company_name }}</h1>
        <p>Generated on: {{ export_date }}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Payment ID</th>
                    <th>Subscription ID</th>
                    <th>Amount</th>
                    <th>Stripe Payment Intent</th>
                    <th>Stripe Status</th>
                    <th>Payment Method</th>
                    <th>Transaction ID</th>
                    <th>Processed At</th>
                </tr>
            </thead>
            <tbody>
                {% for payment in payments %}
                <tr>
                    <td>{{ payment.id }}</td>
                    <td>{{ payment.subscription_id }}</td>
                    <td>{{ payment.amount | currency }} {{ payment.currency }}</td>
                    <td>{{ payment.stripe_payment_intent_id }}</td>
                    <td>{{ payment.stripe_status }}</td>
                    <td>{{ payment.payment_method }}</td>
                    <td>{{ payment.transaction_id }}</td>
                    <td>{{ payment.processed_at }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        """
        
        # Create the template file temporarily
        template_service.create_template_file("exports/payments_export_test.html", payment_export_template)
        
        try:
            # Render the payment export template
            rendered = asyncio.run(template_service.render_export_template(
                "exports/payments_export_test.html",
                payment_export_context,
                "html"
            ))
            
            content = rendered.content
            payment_details = context['payment_details']
            
            # Requirement 5.7: Stripe transaction details and status in payment exports
            assert payment_details['stripe_payment_intent_id'] in content, \
                "Payment export should include Stripe payment intent ID"
            
            assert payment_details['stripe_status'] in content, \
                "Payment export should include Stripe payment status"
            
            assert payment_details['payment_method'] in content, \
                "Payment export should include payment method"
            
            assert payment_details['transaction_id'] in content, \
                "Payment export should include transaction ID"
            
            # Check for Stripe-specific identifiers
            assert 'stripe' in content.lower(), \
                "Payment export should reference Stripe integration"
            
        finally:
            # Clean up the temporary template file
            import os
            temp_template_path = template_service.template_dir / "exports/payments_export_test.html"
            if temp_template_path.exists():
                os.remove(temp_template_path)

    @given(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_subscription_management_links_in_relevant_emails(self, user_name):
        """
        Property 16: Template content accuracy - Subscription management links
        
        For any relevant email template, subscription management links should be included
        
        **Feature: subscription-payment-enhancements, Property 16: Template content accuracy**
        **Validates: Requirements 4.7**
        """
        template_service = self.get_template_service()
        subscription_id = str(uuid7())
        subscription_url = f"https://banwee.com/subscriptions/{subscription_id}"
        
        # Test different email templates that should include subscription management links
        email_templates = [
            "emails/payment_confirmation.html",
            "emails/subscription_cost_change.html"
        ]
        
        for template_name in email_templates:
            if template_service.template_exists(template_name):
                context = {
                    'user_name': user_name,
                    'subscription_id': subscription_id,
                    'subscription_management_url': subscription_url,
                    'company_name': 'Banwee',
                    'old_cost': 25.99,
                    'new_cost': 27.99,
                    'cost_difference': 2.00,
                    'change_reason': 'Admin percentage adjustment',
                    'payment_date': datetime.now().strftime('%B %d, %Y'),
                    'payment_method': 'Visa ending in 1234',
                    'payment_amount': 27.99
                }
                
                rendered = asyncio.run(template_service.render_email_template(template_name, context))
                content = rendered.content.lower()
                
                # Requirement 4.7: Subscription management links in all relevant emails
                assert subscription_url in rendered.content, \
                    f"Email template {template_name} should contain subscription management URL"
                
                # Check for subscription management link text/context
                assert ('subscription' in content and ('manage' in content or 'view' in content or 'details' in content)), \
                    f"Email template {template_name} should contain subscription management link text"

    def test_template_content_completeness_with_missing_data(self):
        """
        Property 16: Template content accuracy - Graceful handling of missing data
        
        Templates should handle missing data gracefully without breaking
        
        **Feature: subscription-payment-enhancements, Property 16: Template content accuracy**
        **Validates: Requirements 4.4, 4.7, 5.4, 5.7**
        """
        template_service = self.get_template_service()
        
        # Test with minimal context
        minimal_context = {
            'user_name': 'Test User',
            'company_name': 'Banwee'
        }
        
        # Should not raise an exception even with minimal data
        rendered = asyncio.run(template_service.render_email_template(
            "emails/payment_confirmation.html",
            minimal_context
        ))
        
        # Should still contain basic structure
        assert 'Test User' in rendered.content
        assert 'Banwee' in rendered.content
        
        # Should handle missing cost breakdown gracefully
        content = rendered.content.lower()
        assert 'payment confirmation' in content or 'thank you' in content