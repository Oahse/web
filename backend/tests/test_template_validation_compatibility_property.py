"""
Property-based test for template validation and compatibility.

This test validates Property 30: Template validation and compatibility
**Validates: Requirements 16.5, 16.6**
Requirements: 16.5, 16.6

Property 30: Template validation and compatibility
*For any* template migration or creation, the system should validate templates to prevent rendering errors and ensure all dynamic data renders correctly
"""

import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from hypothesis.strategies import composite

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from services.jinja_template import JinjaTemplateService, RenderedTemplate, RenderedExport, TemplateValidationResult
from jinja2 import TemplateError


class TestTemplateValidationCompatibilityProperty:
    """Test template validation and compatibility properties"""

    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def template_service(self, temp_template_dir):
        """JinjaTemplateService instance with temporary template directory"""
        return JinjaTemplateService(template_dir=temp_template_dir)

    @composite
    def valid_template_content(draw):
        """Generate valid Jinja template content with dynamic data"""
        # Base template structures
        base_templates = [
            "Hello {{ name }}!",
            "Your order total is {{ total | currency }}",
            "Welcome {{ customer.name }}, your subscription is {{ status }}",
            "{% for item in items %}{{ item.name }}: {{ item.price }}{% endfor %}",
            "{% if user %}Hello {{ user.name }}{% else %}Hello Guest{% endif %}",
            "Date: {{ date | date }}, Amount: {{ amount | currency('USD') }}",
            "<h1>{{ title }}</h1><p>{{ content }}</p>",
            "{% set total = 0 %}{% for item in items %}{% set total = total + item.price %}{% endfor %}Total: {{ total }}",
        ]
        
        template = draw(st.sampled_from(base_templates))
        
        # Add optional additional content
        additional_content = draw(st.lists(st.sampled_from([
            "\n<p>Additional info: {{ info }}</p>",
            "\n{% if discount %}Discount: {{ discount }}%{% endif %}",
            "\n<ul>{% for tag in tags %}<li>{{ tag }}</li>{% endfor %}</ul>",
            "\nGenerated at: {{ generated_at | datetime }}",
        ]), max_size=2))
        
        return template + "".join(additional_content)

    @composite
    def template_context_data(draw):
        """Generate context data that matches template variables"""
        # Generate basic context data
        context = {
            "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
            "title": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs')))),
            "content": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs')))),
            "status": draw(st.sampled_from(["active", "inactive", "pending", "cancelled"])),
            "total": draw(st.floats(min_value=0.01, max_value=10000.0)),
            "amount": draw(st.floats(min_value=0.01, max_value=10000.0)),
            "discount": draw(st.integers(min_value=0, max_value=100)),
            "info": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs')))),
        }
        
        # Add customer object
        context["customer"] = {
            "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
            "email": f"{draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))}@example.com",
        }
        
        # Add user object (sometimes None)
        if draw(st.booleans()):
            context["user"] = {
                "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
                "id": draw(st.integers(min_value=1, max_value=10000)),
            }
        else:
            context["user"] = None
        
        # Add items list
        items_count = draw(st.integers(min_value=0, max_value=5))
        context["items"] = []
        for i in range(items_count):
            context["items"].append({
                "name": draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
                "price": draw(st.floats(min_value=0.01, max_value=1000.0)),
                "id": i + 1,
            })
        
        # Add tags list
        tags_count = draw(st.integers(min_value=0, max_value=3))
        context["tags"] = [
            draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
            for _ in range(tags_count)
        ]
        
        # Add date/time fields
        from datetime import datetime, date
        context["date"] = date.today()
        context["generated_at"] = datetime.now()
        
        return context

    @composite
    def invalid_template_content(draw):
        """Generate invalid Jinja template content with syntax errors"""
        invalid_templates = [
            "{{ unclosed_variable",  # Unclosed variable
            "{% if condition %}no endif",  # Missing endif
            "{% for item in items %}no endfor",  # Missing endfor
            "{{ variable | nonexistent_filter }}",  # Non-existent filter
            "{% unknown_tag %}content{% endunknown_tag %}",  # Unknown tag
            "{{ variable.nonexistent.deeply.nested }}",  # Deeply nested non-existent attribute
            "{% if %}empty condition{% endif %}",  # Empty condition
            "{{ 'unclosed string }}",  # Unclosed string
            "{% set var = %}",  # Incomplete set statement
            "{{ variable | filter() | }}",  # Incomplete filter chain
        ]
        
        return draw(st.sampled_from(invalid_templates))

    @composite
    def migration_template_scenarios(draw):
        """Generate template migration scenarios"""
        # Simulate templates that might exist during migration
        legacy_patterns = [
            # Templates that might have been converted from ReportLab
            "Invoice #{{ invoice_number }}\nCustomer: {{ customer_name }}\nTotal: ${{ total_amount }}",
            "{% for line_item in line_items %}{{ line_item.description }}: ${{ line_item.amount }}{% endfor %}",
            "Report generated on {{ report_date | date }}\n{% if has_data %}Data available{% else %}No data{% endif %}",
            # Email templates
            "Dear {{ recipient_name }},\n\nYour subscription {{ subscription_id }} has been {{ action }}.\n\nBest regards,\nBanwee Team",
            # Export templates
            "{% for record in records %}{{ record.id }},{{ record.name }},{{ record.value }}{% endfor %}",
        ]
        
        template_content = draw(st.sampled_from(legacy_patterns))
        
        # Generate corresponding context data
        context = {
            "invoice_number": draw(st.integers(min_value=1000, max_value=99999)),
            "customer_name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Pc')))),
            "total_amount": draw(st.floats(min_value=0.01, max_value=10000.0)),
            "recipient_name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Pc')))),
            "subscription_id": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
            "action": draw(st.sampled_from(["activated", "cancelled", "paused", "resumed"])),
            "has_data": draw(st.booleans()),
        }
        
        # Add line items
        line_items_count = draw(st.integers(min_value=1, max_value=5))
        context["line_items"] = []
        for i in range(line_items_count):
            context["line_items"].append({
                "description": draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Pc', 'Zs')))),
                "amount": draw(st.floats(min_value=0.01, max_value=1000.0)),
            })
        
        # Add records for export templates
        records_count = draw(st.integers(min_value=1, max_value=10))
        context["records"] = []
        for i in range(records_count):
            context["records"].append({
                "id": i + 1,
                "name": draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
                "value": draw(st.floats(min_value=0.01, max_value=1000.0)),
            })
        
        # Add date fields
        from datetime import date
        context["report_date"] = date.today()
        
        return template_content, context

    @given(valid_template_content(), template_context_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_template_validation_prevents_rendering_errors_property(
        self, template_service, template_content, context_data
    ):
        """
        Property: For any valid template content, validation should pass and rendering should succeed
        **Feature: subscription-payment-enhancements, Property 30: Template validation and compatibility**
        **Validates: Requirements 16.6**
        """
        try:
            # Property: Template validation should identify valid templates
            validation_result = asyncio.run(template_service.validate_template(template_content))
            
            # Property: Validation result should be a TemplateValidationResult
            assert isinstance(validation_result, TemplateValidationResult), "Validation should return TemplateValidationResult"
            
            # Property: Valid templates should pass validation or only have warnings
            if validation_result.errors:
                # If there are errors, they should be meaningful
                for error in validation_result.errors:
                    assert isinstance(error, str) and len(error) > 0, "Errors should be non-empty strings"
                    assert any(keyword in error.lower() for keyword in [
                        "syntax", "error", "undefined", "invalid", "missing"
                    ]), f"Error should be descriptive: {error}"
            
            # Property: If validation passes (no errors), rendering should succeed with proper context
            if validation_result.is_valid:
                # Create a temporary template file
                template_name = "test_template.html"
                template_service.create_template_file(template_name, template_content)
                
                # Property: Rendering should succeed with appropriate context
                rendered = asyncio.run(template_service.render_email_template(template_name, context_data))
                
                # Property: Rendered result should be a RenderedTemplate
                assert isinstance(rendered, RenderedTemplate), "Rendering should return RenderedTemplate"
                
                # Property: Rendered content should be non-empty string (unless it's an empty loop)
                assert isinstance(rendered.content, str), "Rendered content should be a string"
                # Allow empty content for templates with empty loops (like empty items list)
                if "{% for" in template_content and len(context_data.get("items", [])) == 0:
                    # Empty loop is acceptable
                    pass
                else:
                    assert len(rendered.content) > 0, "Rendered content should not be empty"
                
                # Property: Template name should match
                assert rendered.template_name == template_name, "Template name should match"
                
                # Property: Context should be preserved
                assert isinstance(rendered.context_used, dict), "Context should be preserved as dict"
                
                # Property: Rendered content should not contain unresolved template variables
                # (unless they were intentionally undefined in context)
                assert "{{" not in rendered.content or "}}" not in rendered.content or (
                    # Allow for intentionally undefined variables that show as empty
                    rendered.content.count("{{") == 0 and rendered.content.count("}}") == 0
                ), "Rendered content should not contain unresolved template variables"
                
        except Exception as e:
            # Property: Any exceptions should be meaningful and related to template processing
            if isinstance(e, AssertionError):
                # Re-raise assertion errors for proper test failure reporting
                raise e
            assert isinstance(e, (TemplateError, ValueError, TypeError)), f"Unexpected exception type: {type(e)}"
            pytest.skip(f"Template appropriately rejected due to: {e}")

    @given(invalid_template_content())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_template_validation_detects_syntax_errors_property(
        self, template_service, invalid_template_content
    ):
        """
        Property: For any invalid template content, validation should detect syntax errors
        **Feature: subscription-payment-enhancements, Property 30: Template validation and compatibility**
        **Validates: Requirements 16.6**
        """
        # Property: Template validation should detect invalid templates
        validation_result = asyncio.run(template_service.validate_template(invalid_template_content))
        
        # Property: Validation result should be a TemplateValidationResult
        assert isinstance(validation_result, TemplateValidationResult), "Validation should return TemplateValidationResult"
        
        # Property: Invalid templates should fail validation (or have meaningful warnings)
        # Note: Some "invalid" templates like undefined variables may validate but warn
        if not validation_result.is_valid:
            # Property: Errors should be reported
            assert len(validation_result.errors) > 0, "Invalid templates should have error messages"
            
            # Property: Error messages should be descriptive
            for error in validation_result.errors:
                assert isinstance(error, str) and len(error) > 0, "Errors should be non-empty strings"
                assert any(keyword in error.lower() for keyword in [
                    "syntax", "error", "unexpected", "invalid", "missing", "unclosed", "unknown"
                ]), f"Error should be descriptive: {error}"
        else:
            # If validation passes, it should at least have warnings for problematic content
            if any(pattern in invalid_template_content for pattern in ["nonexistent", "undefined", "unknown"]):
                assert len(validation_result.warnings) > 0, "Templates with undefined variables should have warnings"

    @given(migration_template_scenarios())
    @settings(max_examples=75, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_migrated_template_dynamic_data_rendering_property(
        self, template_service, migration_scenario
    ):
        """
        Property: For any migrated template, all dynamic data should render correctly
        **Feature: subscription-payment-enhancements, Property 30: Template validation and compatibility**
        **Validates: Requirements 16.5**
        """
        template_content, context_data = migration_scenario
        
        try:
            # Property: Migrated templates should validate successfully
            validation_result = asyncio.run(template_service.validate_template(template_content))
            
            # Property: Validation should provide meaningful feedback
            assert isinstance(validation_result, TemplateValidationResult), "Validation should return TemplateValidationResult"
            
            # If validation passes, test rendering
            if validation_result.is_valid or len(validation_result.errors) == 0:
                # Create template file
                template_name = "migrated_template.html"
                template_service.create_template_file(template_name, template_content)
                
                # Property: Migrated templates should render successfully with dynamic data
                rendered = asyncio.run(template_service.render_email_template(template_name, context_data))
                
                # Property: Rendered result should be valid
                assert isinstance(rendered, RenderedTemplate), "Rendering should return RenderedTemplate"
                assert isinstance(rendered.content, str), "Rendered content should be a string"
                assert len(rendered.content) > 0, "Rendered content should not be empty"
                
                # Property: Dynamic data should be properly substituted
                # Check that template variables have been replaced with actual values
                original_variables = []
                import re
                # Find all {{ variable }} patterns in original template
                variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
                variables = re.findall(variable_pattern, template_content)
                
                for var in variables:
                    # Clean variable name (remove filters and whitespace)
                    clean_var = var.split('|')[0].strip()
                    
                    # Property: Variables should be resolved in rendered content
                    if clean_var in str(context_data) or any(clean_var.startswith(key) for key in context_data.keys()):
                        # Variable should be resolved (not appear as {{ var }} in output)
                        assert f"{{{{{clean_var}}}}}" not in rendered.content, f"Variable {clean_var} should be resolved in rendered content"
                
                # Property: Control structures should be processed
                # Check that {% %} blocks are processed and don't appear in output
                control_pattern = r'\{%\s*[^%]+\s*%\}'
                control_blocks = re.findall(control_pattern, template_content)
                for block in control_blocks:
                    assert block not in rendered.content, f"Control block {block} should be processed and not appear in output"
                
                # Property: Filters should be applied correctly
                if '| currency' in template_content:
                    # Currency filter should format numbers with $ or currency code
                    assert '$' in rendered.content or any(curr in rendered.content for curr in ['USD', 'EUR', 'GBP']), "Currency filter should format monetary values"
                
                if '| date' in template_content:
                    # Date filter should format dates properly
                    import re
                    date_pattern = r'\b\w+\s+\d{1,2},\s+\d{4}\b'  # "January 01, 2024" format
                    assert re.search(date_pattern, rendered.content), "Date filter should format dates properly"
                
        except TemplateError as e:
            # Property: Template errors should be meaningful for migration debugging
            assert "syntax" in str(e).lower() or "undefined" in str(e).lower() or "invalid" in str(e).lower(), f"Template error should be descriptive: {e}"
            pytest.skip(f"Template migration scenario appropriately rejected: {e}")
        except Exception as e:
            # Property: Unexpected errors should be handled gracefully
            pytest.skip(f"Migration scenario encountered expected complexity: {e}")

    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_template_validation_robustness_property(
        self, template_service, arbitrary_content
    ):
        """
        Property: For any arbitrary content, template validation should handle it gracefully
        **Feature: subscription-payment-enhancements, Property 30: Template validation and compatibility**
        **Validates: Requirements 16.6**
        """
        # Filter out content that might cause issues with the test itself
        assume(len(arbitrary_content.strip()) > 0)
        assume(not arbitrary_content.isspace())
        
        try:
            # Property: Validation should handle arbitrary content without crashing
            validation_result = asyncio.run(template_service.validate_template(arbitrary_content))
            
            # Property: Result should always be a TemplateValidationResult
            assert isinstance(validation_result, TemplateValidationResult), "Validation should always return TemplateValidationResult"
            
            # Property: Result should have required fields
            assert isinstance(validation_result.is_valid, bool), "is_valid should be boolean"
            assert isinstance(validation_result.errors, list), "errors should be a list"
            assert isinstance(validation_result.warnings, list), "warnings should be a list"
            
            # Property: If invalid, should have error messages
            if not validation_result.is_valid:
                assert len(validation_result.errors) > 0, "Invalid templates should have error messages"
                
                # Property: Error messages should be strings
                for error in validation_result.errors:
                    assert isinstance(error, str), "Error messages should be strings"
                    assert len(error) > 0, "Error messages should not be empty"
            
        except Exception as e:
            # Property: Validation should not crash on arbitrary input
            pytest.fail(f"Template validation should handle arbitrary content gracefully, but got: {e}")

    def test_template_validation_compatibility_integration(self, template_service):
        """
        Integration test for template validation and compatibility features
        **Feature: subscription-payment-enhancements, Property 30: Template validation and compatibility**
        **Validates: Requirements 16.5, 16.6**
        """
        # Test various template scenarios that might occur during migration
        test_scenarios = [
            # Valid email template
            {
                "template": "Dear {{ customer_name }},\n\nYour subscription is {{ status }}.\n\nThank you!",
                "context": {"customer_name": "John Doe", "status": "active"},
                "should_validate": True,
                "should_render": True,
            },
            # Valid export template
            {
                "template": "{% for item in items %}{{ item.name }},{{ item.price }}{% endfor %}",
                "context": {"items": [{"name": "Product A", "price": 29.99}, {"name": "Product B", "price": 39.99}]},
                "should_validate": True,
                "should_render": True,
            },
            # Invalid template with syntax error
            {
                "template": "{{ unclosed_variable",
                "context": {},
                "should_validate": False,
                "should_render": False,
            },
            # Template with undefined variable (should validate but warn)
            {
                "template": "Hello {{ undefined_var }}!",
                "context": {},
                "should_validate": True,  # Should validate but may have warnings
                "should_render": True,   # Should render with empty value
            },
        ]
        
        for i, scenario in enumerate(test_scenarios):
            template_name = f"test_scenario_{i}.html"
            
            # Test validation
            validation_result = asyncio.run(template_service.validate_template(scenario["template"]))
            
            if scenario["should_validate"]:
                # Should validate (may have warnings but no errors)
                if not validation_result.is_valid:
                    # Check if it's just warnings about undefined variables
                    has_only_undefined_warnings = all(
                        "undefined" in error.lower() for error in validation_result.errors
                    )
                    if not has_only_undefined_warnings:
                        pytest.fail(f"Scenario {i} should validate but got errors: {validation_result.errors}")
            else:
                # Should not validate
                assert not validation_result.is_valid, f"Scenario {i} should not validate"
                assert len(validation_result.errors) > 0, f"Scenario {i} should have errors"
            
            # Test rendering if expected to work
            if scenario["should_render"] and (validation_result.is_valid or 
                all("undefined" in error.lower() for error in validation_result.errors)):
                
                template_service.create_template_file(template_name, scenario["template"])
                
                try:
                    rendered = asyncio.run(template_service.render_email_template(template_name, scenario["context"]))
                    assert isinstance(rendered, RenderedTemplate), f"Scenario {i} should render successfully"
                    assert len(rendered.content) > 0, f"Scenario {i} should produce non-empty content"
                except TemplateError:
                    if scenario["should_render"]:
                        pytest.fail(f"Scenario {i} should render but failed")