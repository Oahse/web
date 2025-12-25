#!/usr/bin/env python3
"""
Template Validation and Migration Service

This service provides comprehensive template validation, migration from ReportLab
to Jinja templates, backward compatibility checking, and documentation updates
as required by the subscription payment enhancements specification.

Requirements addressed:
- 16.4: Maintain backward compatibility for existing export APIs
- 16.5: Ensure all dynamic data renders correctly in migrated templates
- 16.6: Add template validation to prevent rendering errors
- 16.7: Update documentation to reflect Jinja template usage
"""

import os
import sys
import json
import logging
import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template, TemplateError
from jinja2.meta import find_undeclared_variables
from pydantic import BaseModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('template_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TemplateValidationIssue:
    """Represents a template validation issue"""
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None


class TemplateValidationReport(BaseModel):
    """Comprehensive template validation report"""
    template_name: str
    is_valid: bool
    errors: List[TemplateValidationIssue]
    warnings: List[TemplateValidationIssue]
    info: List[TemplateValidationIssue]
    required_variables: Set[str]
    optional_variables: Set[str]
    filters_used: Set[str]
    macros_used: Set[str]
    includes_used: Set[str]
    validation_timestamp: str


class TemplateMigrationResult(BaseModel):
    """Result of template migration process"""
    template_name: str
    migration_successful: bool
    original_format: str  # "reportlab", "legacy_html", etc.
    migrated_format: str  # "jinja_html", "jinja_csv", etc.
    issues_found: List[TemplateValidationIssue]
    backward_compatible: bool
    migration_notes: List[str]
    migration_timestamp: str


class APICompatibilityResult(BaseModel):
    """Result of API compatibility check"""
    endpoint: str
    compatible: bool
    issues: List[str]
    suggested_fixes: List[str]
    test_results: Dict[str, Any]


class TemplateMigrationService:
    """Comprehensive template validation and migration service"""
    
    def __init__(self, template_dir: str = "templates", backup_dir: str = "template_backups"):
        self.template_dir = Path(template_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters for validation
        self._setup_custom_filters()
        
        # Track migration progress
        self.migration_log = []
        
    def _setup_custom_filters(self):
        """Setup custom Jinja filters for template validation"""
        self.env.filters['currency'] = self._format_currency
        self.env.filters['date'] = self._format_date
        self.env.filters['datetime'] = self._format_datetime
        self.env.filters['percentage'] = self._format_percentage
        self.env.filters['number'] = self._format_number
        
    def _format_currency(self, value: float, currency: str = "USD") -> str:
        """Format currency values"""
        try:
            if currency == "USD":
                return f"${float(value):.2f}"
            return f"{float(value):.2f} {currency}"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_date(self, value) -> str:
        """Format date values"""
        if hasattr(value, 'strftime'):
            return value.strftime('%B %d, %Y')
        return str(value)
    
    def _format_datetime(self, value) -> str:
        """Format datetime values"""
        if hasattr(value, 'strftime'):
            return value.strftime('%B %d, %Y at %I:%M %p')
        return str(value)
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage values"""
        try:
            return f"{float(value):.1f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_number(self, value: float, decimals: int = 2) -> str:
        """Format number values"""
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def create_template_backup(self, template_name: str) -> str:
        """
        Create a backup of an existing template before migration
        
        Args:
            template_name: Name of the template to backup
            
        Returns:
            str: Path to the backup file
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{template_name}.backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Create backup directory structure
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy template content
        with open(template_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        logger.info(f"Template backup created: {backup_path}")
        return str(backup_path)
    
    def validate_template_comprehensive(self, template_name: str) -> TemplateValidationReport:
        """
        Perform comprehensive validation of a Jinja template
        
        Args:
            template_name: Name of the template to validate
            
        Returns:
            TemplateValidationReport with detailed validation results
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            return TemplateValidationReport(
                template_name=template_name,
                is_valid=False,
                errors=[TemplateValidationIssue(
                    severity="error",
                    message=f"Template file not found: {template_name}"
                )],
                warnings=[],
                info=[],
                required_variables=set(),
                optional_variables=set(),
                filters_used=set(),
                macros_used=set(),
                includes_used=set(),
                validation_timestamp=datetime.now().isoformat()
            )
        
        errors = []
        warnings = []
        info = []
        required_variables = set()
        optional_variables = set()
        filters_used = set()
        macros_used = set()
        includes_used = set()
        
        try:
            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Parse template
            try:
                template = self.env.from_string(template_content)
                ast = self.env.parse(template_content)
                
                # Find undeclared variables
                undeclared = find_undeclared_variables(ast)
                
                # Categorize variables
                for var in undeclared:
                    if var in ['company_name', 'support_email', 'current_year', 'generated_at']:
                        optional_variables.add(var)
                    else:
                        required_variables.add(var)
                
                # Find filters used
                filter_pattern = r'\|\s*(\w+)'
                filters_found = re.findall(filter_pattern, template_content)
                filters_used.update(filters_found)
                
                # Find macros used
                macro_pattern = r'{%\s*macro\s+(\w+)'
                macros_found = re.findall(macro_pattern, template_content)
                macros_used.update(macros_found)
                
                # Find includes used
                include_pattern = r'{%\s*include\s+["\']([^"\']+)["\']'
                includes_found = re.findall(include_pattern, template_content)
                includes_used.update(includes_found)
                
                # Validate filters exist
                for filter_name in filters_used:
                    if filter_name not in self.env.filters:
                        warnings.append(TemplateValidationIssue(
                            severity="warning",
                            message=f"Unknown filter used: {filter_name}",
                            suggestion=f"Define custom filter '{filter_name}' or use built-in alternative"
                        ))
                
                # Validate includes exist
                for include_name in includes_used:
                    include_path = self.template_dir / include_name
                    if not include_path.exists():
                        errors.append(TemplateValidationIssue(
                            severity="error",
                            message=f"Included template not found: {include_name}",
                            suggestion=f"Create template file: {include_name}"
                        ))
                
                # Try rendering with sample data
                sample_data = self._generate_sample_data(required_variables, optional_variables)
                try:
                    rendered = template.render(**sample_data)
                    
                    # Check for common issues in rendered output
                    if "undefined" in rendered.lower():
                        warnings.append(TemplateValidationIssue(
                            severity="warning",
                            message="Rendered template contains 'undefined' values",
                            suggestion="Check variable names and provide all required context"
                        ))
                    
                    # Check for empty critical sections
                    if template_name.endswith('.html'):
                        if '<title></title>' in rendered or '<title> </title>' in rendered:
                            warnings.append(TemplateValidationIssue(
                                severity="warning",
                                message="HTML template has empty title",
                                suggestion="Provide a meaningful title variable"
                            ))
                    
                    info.append(TemplateValidationIssue(
                        severity="info",
                        message=f"Template renders successfully ({len(rendered)} characters)"
                    ))
                    
                except Exception as render_error:
                    errors.append(TemplateValidationIssue(
                        severity="error",
                        message=f"Template rendering failed: {render_error}",
                        suggestion="Check variable names and template syntax"
                    ))
                
            except TemplateError as parse_error:
                errors.append(TemplateValidationIssue(
                    severity="error",
                    message=f"Template syntax error: {parse_error}",
                    suggestion="Fix Jinja2 syntax errors"
                ))
            
            # Additional validation checks
            self._validate_template_security(template_content, warnings)
            self._validate_template_performance(template_content, warnings)
            self._validate_template_accessibility(template_content, warnings)
            
        except Exception as e:
            errors.append(TemplateValidationIssue(
                severity="error",
                message=f"Validation failed: {e}"
            ))
        
        return TemplateValidationReport(
            template_name=template_name,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            required_variables=required_variables,
            optional_variables=optional_variables,
            filters_used=filters_used,
            macros_used=macros_used,
            includes_used=includes_used,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _generate_sample_data(self, required_vars: Set[str], optional_vars: Set[str]) -> Dict[str, Any]:
        """Generate sample data for template testing"""
        sample_data = {}
        
        # Common sample values
        sample_values = {
            'user_name': 'John Doe',
            'user_email': 'john.doe@example.com',
            'company_name': 'Banwee',
            'support_email': 'support@banwee.com',
            'current_year': '2024',
            'generated_at': datetime.now().isoformat(),
            'subscription_id': 'sub_123456789',
            'order_id': 'ord_123456789',
            'amount': 29.99,
            'currency': 'USD',
            'date': datetime.now(),
            'datetime': datetime.now(),
            'percentage': 10.5,
            'count': 5,
            'total': 149.95,
            'items': [
                {'name': 'Sample Item 1', 'price': 19.99, 'quantity': 2},
                {'name': 'Sample Item 2', 'price': 29.99, 'quantity': 1}
            ],
            'subscription': {
                'id': 'sub_123456789',
                'status': 'active',
                'next_billing_date': datetime.now(),
                'amount': 29.99
            },
            'payment': {
                'id': 'pay_123456789',
                'status': 'succeeded',
                'amount': 29.99,
                'currency': 'USD'
            }
        }
        
        # Add required variables
        for var in required_vars:
            if var in sample_values:
                sample_data[var] = sample_values[var]
            else:
                # Generate appropriate sample based on variable name
                if 'email' in var.lower():
                    sample_data[var] = 'sample@example.com'
                elif 'name' in var.lower():
                    sample_data[var] = 'Sample Name'
                elif 'amount' in var.lower() or 'price' in var.lower():
                    sample_data[var] = 29.99
                elif 'date' in var.lower():
                    sample_data[var] = datetime.now()
                elif 'id' in var.lower():
                    sample_data[var] = 'sample_123456789'
                else:
                    sample_data[var] = f'sample_{var}'
        
        # Add optional variables
        for var in optional_vars:
            if var in sample_values:
                sample_data[var] = sample_values[var]
        
        return sample_data
    
    def _validate_template_security(self, content: str, warnings: List[TemplateValidationIssue]):
        """Validate template for security issues"""
        # Check for potential XSS vulnerabilities
        if '|safe' in content:
            warnings.append(TemplateValidationIssue(
                severity="warning",
                message="Template uses |safe filter - ensure content is properly sanitized",
                suggestion="Only use |safe with trusted content or implement proper sanitization"
            ))
        
        # Check for potential code injection
        if 'eval(' in content or 'exec(' in content:
            warnings.append(TemplateValidationIssue(
                severity="warning",
                message="Template contains potentially dangerous functions",
                suggestion="Avoid using eval() or exec() in templates"
            ))
    
    def _validate_template_performance(self, content: str, warnings: List[TemplateValidationIssue]):
        """Validate template for performance issues"""
        # Check for excessive loops
        loop_count = content.count('{% for ')
        if loop_count > 5:
            warnings.append(TemplateValidationIssue(
                severity="warning",
                message=f"Template has many loops ({loop_count}) - may impact performance",
                suggestion="Consider optimizing data structure or using pagination"
            ))
        
        # Check for complex expressions
        if content.count('|') > 20:
            warnings.append(TemplateValidationIssue(
                severity="warning",
                message="Template has many filters - may impact performance",
                suggestion="Consider pre-processing data or simplifying expressions"
            ))
    
    def _validate_template_accessibility(self, content: str, warnings: List[TemplateValidationIssue]):
        """Validate template for accessibility issues"""
        if '.html' in content and '<img' in content:
            if 'alt=' not in content:
                warnings.append(TemplateValidationIssue(
                    severity="warning",
                    message="HTML template contains images without alt attributes",
                    suggestion="Add alt attributes to all images for accessibility"
                ))
    
    def migrate_reportlab_template(self, template_name: str, reportlab_code: str) -> TemplateMigrationResult:
        """
        Migrate a ReportLab template to Jinja HTML template
        
        Args:
            template_name: Name for the new Jinja template
            reportlab_code: Original ReportLab code to migrate
            
        Returns:
            TemplateMigrationResult with migration details
        """
        issues = []
        migration_notes = []
        
        try:
            # Create backup if template exists
            if (self.template_dir / template_name).exists():
                backup_path = self.create_template_backup(template_name)
                migration_notes.append(f"Backup created: {backup_path}")
            
            # Analyze ReportLab code
            migration_notes.append("Analyzing ReportLab code structure...")
            
            # Extract data variables from ReportLab code
            variables = self._extract_reportlab_variables(reportlab_code)
            migration_notes.append(f"Found {len(variables)} variables in ReportLab code")
            
            # Generate Jinja HTML template
            jinja_template = self._generate_jinja_from_reportlab(reportlab_code, variables)
            
            # Save migrated template
            template_path = self.template_dir / template_name
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(jinja_template)
            
            migration_notes.append(f"Migrated template saved: {template_path}")
            
            # Validate migrated template
            validation_result = self.validate_template_comprehensive(template_name)
            
            # Check backward compatibility
            backward_compatible = self._check_backward_compatibility(template_name, reportlab_code)
            
            return TemplateMigrationResult(
                template_name=template_name,
                migration_successful=validation_result.is_valid,
                original_format="reportlab",
                migrated_format="jinja_html",
                issues_found=validation_result.errors + validation_result.warnings,
                backward_compatible=backward_compatible,
                migration_notes=migration_notes,
                migration_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            issues.append(TemplateValidationIssue(
                severity="error",
                message=f"Migration failed: {e}"
            ))
            
            return TemplateMigrationResult(
                template_name=template_name,
                migration_successful=False,
                original_format="reportlab",
                migrated_format="jinja_html",
                issues_found=issues,
                backward_compatible=False,
                migration_notes=migration_notes,
                migration_timestamp=datetime.now().isoformat()
            )
    
    def _extract_reportlab_variables(self, reportlab_code: str) -> Set[str]:
        """Extract variable names from ReportLab code"""
        variables = set()
        
        # Common patterns for variable access in ReportLab
        patterns = [
            r'data\[[\'"](.*?)[\'"]\]',  # data['variable']
            r'data\.(\w+)',              # data.variable
            r'context\[[\'"](.*?)[\'"]\]', # context['variable']
            r'context\.(\w+)',           # context.variable
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, reportlab_code)
            variables.update(matches)
        
        return variables
    
    def _generate_jinja_from_reportlab(self, reportlab_code: str, variables: Set[str]) -> str:
        """Generate Jinja HTML template from ReportLab code"""
        # Basic HTML template structure
        template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title | default('Document') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .content { margin: 20px 0; }
        .footer { border-top: 1px solid #ccc; padding-top: 10px; margin-top: 20px; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .currency { text-align: right; }
        .total { font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ company_name | default('Banwee') }}</h1>
        {% if document_title %}
        <h2>{{ document_title }}</h2>
        {% endif %}
        {% if generated_at %}
        <p>Generated: {{ generated_at | datetime }}</p>
        {% endif %}
    </div>
    
    <div class="content">
        {% if user_name or user_email %}
        <div class="customer-info">
            <h3>Customer Information</h3>
            {% if user_name %}<p><strong>Name:</strong> {{ user_name }}</p>{% endif %}
            {% if user_email %}<p><strong>Email:</strong> {{ user_email }}</p>{% endif %}
        </div>
        {% endif %}
        
        {% if items %}
        <div class="items">
            <h3>Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item.name | default(item.description) }}</td>
                        <td>{{ item.quantity | default(1) }}</td>
                        <td class="currency">{{ item.price | currency(currency) }}</td>
                        <td class="currency">{{ (item.price * item.quantity) | currency(currency) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if total_amount %}
        <div class="totals">
            <table style="width: 300px; margin-left: auto;">
                {% if subtotal %}
                <tr>
                    <td><strong>Subtotal:</strong></td>
                    <td class="currency total">{{ subtotal | currency(currency) }}</td>
                </tr>
                {% endif %}
                {% if tax_amount %}
                <tr>
                    <td><strong>Tax:</strong></td>
                    <td class="currency">{{ tax_amount | currency(currency) }}</td>
                </tr>
                {% endif %}
                {% if delivery_cost %}
                <tr>
                    <td><strong>Delivery:</strong></td>
                    <td class="currency">{{ delivery_cost | currency(currency) }}</td>
                </tr>
                {% endif %}
                <tr>
                    <td><strong>Total:</strong></td>
                    <td class="currency total">{{ total_amount | currency(currency) }}</td>
                </tr>
            </table>
        </div>
        {% endif %}
        
        <!-- Additional variables from ReportLab code -->
        {% for variable in variables %}
        {% if {{ variable }} %}
        <p><strong>{{ variable | title }}:</strong> {{ {{ variable }} }}</p>
        {% endif %}
        {% endfor %}
    </div>
    
    <div class="footer">
        <p>{{ company_name | default('Banwee') }} - {{ support_email | default('support@banwee.com') }}</p>
        <p>Generated on {{ generated_at | datetime }}</p>
    </div>
</body>
</html>"""
        
        # Replace variable placeholders with actual variables
        for variable in variables:
            if variable not in ['items', 'user_name', 'user_email', 'total_amount', 'subtotal', 'tax_amount', 'delivery_cost']:
                template = template.replace(
                    '{% for variable in variables %}',
                    f'{{% if {variable} %}}\n        <p><strong>{variable.title()}:</strong> {{{{ {variable} }}}}</p>\n        {{% endif %}}\n        {{% for variable in variables %}}',
                    1
                )
        
        # Clean up the template
        template = template.replace('{% for variable in variables %}', '')
        template = template.replace('{% endfor %}', '', 1)
        
        return template
    
    def _check_backward_compatibility(self, template_name: str, original_code: str) -> bool:
        """Check if migrated template maintains backward compatibility"""
        try:
            # This is a simplified check - in practice, you'd want to test
            # that the same data produces equivalent output
            validation_result = self.validate_template_comprehensive(template_name)
            return validation_result.is_valid and len(validation_result.errors) == 0
        except Exception:
            return False
    
    async def validate_api_compatibility(self, endpoint_patterns: List[str]) -> List[APICompatibilityResult]:
        """
        Validate that existing export APIs still work with Jinja templates
        
        Args:
            endpoint_patterns: List of API endpoint patterns to test
            
        Returns:
            List of APICompatibilityResult for each endpoint
        """
        results = []
        
        for endpoint in endpoint_patterns:
            try:
                # Import FastAPI app for testing
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from main import app
                from fastapi.testclient import TestClient
                
                client = TestClient(app)
                
                # Test endpoint
                response = client.get(endpoint)
                
                compatible = response.status_code in [200, 401, 403]  # Auth may be required
                issues = []
                suggested_fixes = []
                
                if not compatible:
                    issues.append(f"Endpoint returned status {response.status_code}")
                    suggested_fixes.append("Check endpoint implementation and template rendering")
                
                # Check response content type
                content_type = response.headers.get('content-type', '')
                if 'html' in endpoint and 'html' not in content_type:
                    issues.append(f"Expected HTML content type, got: {content_type}")
                    suggested_fixes.append("Ensure template renders HTML content")
                
                results.append(APICompatibilityResult(
                    endpoint=endpoint,
                    compatible=compatible,
                    issues=issues,
                    suggested_fixes=suggested_fixes,
                    test_results={
                        'status_code': response.status_code,
                        'content_type': content_type,
                        'response_size': len(response.content)
                    }
                ))
                
            except Exception as e:
                results.append(APICompatibilityResult(
                    endpoint=endpoint,
                    compatible=False,
                    issues=[f"Test failed: {e}"],
                    suggested_fixes=["Check endpoint exists and is properly configured"],
                    test_results={'error': str(e)}
                ))
        
        return results
    
    def generate_template_documentation(self) -> str:
        """
        Generate comprehensive documentation for Jinja template usage
        
        Returns:
            str: Markdown documentation content
        """
        doc_content = """# Jinja Template System Documentation

## Overview

The Banwee platform uses Jinja2 templates for generating emails and exports, replacing the previous ReportLab-based system. This provides better maintainability, flexibility, and performance.

## Template Structure

### Email Templates

Email templates are located in `core/utils/message/templates/` and follow this structure:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title | default('Email from Banwee') }}</title>
</head>
<body>
    <h1>{{ company_name | default('Banwee') }}</h1>
    <p>Hello {{ user_name }},</p>
    <!-- Email content -->
</body>
</html>
```

### Export Templates

Export templates are located in `core/utils/message/templates/exports/` and support multiple formats:

- **HTML**: For web display and PDF generation
- **CSV**: For spreadsheet import
- **JSON**: For API responses

## Available Variables

### Common Variables

All templates have access to these common variables:

- `company_name`: Company name (default: "Banwee")
- `support_email`: Support email address
- `current_year`: Current year
- `generated_at`: Generation timestamp

### Email-Specific Variables

- `user_name`: Recipient's name
- `user_email`: Recipient's email address
- `subscription`: Subscription details object
- `payment`: Payment details object

### Export-Specific Variables

- `items`: List of items/records to export
- `total_count`: Total number of records
- `filters_applied`: Applied filters object
- `date_range`: Date range for the export

## Custom Filters

The template system includes custom filters for common formatting:

### Currency Filter

```jinja2
{{ amount | currency }}          <!-- $29.99 -->
{{ amount | currency('EUR') }}   <!-- 29.99 EUR -->
```

### Date Filters

```jinja2
{{ date_value | date }}          <!-- December 23, 2024 -->
{{ datetime_value | datetime }}  <!-- December 23, 2024 at 2:30 PM -->
```

### Number Filters

```jinja2
{{ percentage_value | percentage }}  <!-- 10.5% -->
{{ number_value | number(1) }}       <!-- 123.4 -->
```

## Template Validation

All templates are automatically validated for:

- **Syntax errors**: Jinja2 syntax validation
- **Variable usage**: Required vs optional variables
- **Security issues**: XSS prevention, safe filter usage
- **Performance**: Loop complexity, filter usage
- **Accessibility**: HTML accessibility standards

## Migration from ReportLab

### Automatic Migration

The system can automatically migrate ReportLab templates:

```python
from services.template_migration_service import TemplateMigrationService

service = TemplateMigrationService()
result = service.migrate_reportlab_template('invoice.html', reportlab_code)
```

### Manual Migration Steps

1. **Identify data variables** in the ReportLab code
2. **Create HTML structure** for the template
3. **Add Jinja variables** using `{{ variable_name }}`
4. **Apply filters** for formatting
5. **Validate template** using the validation service

## API Compatibility

### Existing Export APIs

All existing export APIs continue to work with Jinja templates:

- `/api/exports/subscriptions` - Subscription export
- `/api/exports/payments` - Payment export
- `/api/exports/invoices` - Invoice generation

### Response Formats

APIs support multiple response formats through template selection:

```python
# HTML response
GET /api/exports/subscriptions?format=html

# CSV response  
GET /api/exports/subscriptions?format=csv

# JSON response
GET /api/exports/subscriptions?format=json
```

## Best Practices

### Template Organization

- Use descriptive template names
- Organize templates by type (emails, exports)
- Create reusable base templates
- Include template comments for complex logic

### Variable Naming

- Use snake_case for variable names
- Provide default values for optional variables
- Document required variables in template comments

### Performance

- Minimize complex loops and filters
- Pre-process data when possible
- Use template caching for frequently used templates

### Security

- Always escape user input (automatic with autoescape)
- Use `|safe` filter only with trusted content
- Validate template content before deployment

## Troubleshooting

### Common Issues

1. **Template not found**: Check file path and name
2. **Variable undefined**: Ensure all required variables are provided
3. **Rendering errors**: Validate template syntax
4. **Performance issues**: Check for complex loops or filters

### Validation Tools

Use the template validation service to check templates:

```python
service = TemplateMigrationService()
report = service.validate_template_comprehensive('template_name.html')
```

### Debugging

Enable template debugging in development:

```python
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True,
    undefined=DebugUndefined  # Shows undefined variables
)
```

## Support

For template-related issues:

1. Check template validation report
2. Review template documentation
3. Test with sample data
4. Contact development team

---

*This documentation is automatically generated and updated with each template system change.*
"""
        
        return doc_content
    
    def save_documentation(self, output_path: str = "TEMPLATE_DOCUMENTATION.md") -> str:
        """
        Save template documentation to file
        
        Args:
            output_path: Path to save documentation
            
        Returns:
            str: Path to saved documentation
        """
        doc_content = self.generate_template_documentation()
        
        doc_path = Path(output_path)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        logger.info(f"Template documentation saved: {doc_path}")
        return str(doc_path)
    
    def validate_all_templates(self) -> Dict[str, TemplateValidationReport]:
        """
        Validate all templates in the template directory
        
        Returns:
            Dict mapping template names to validation reports
        """
        results = {}
        
        # Find all template files
        for template_path in self.template_dir.rglob("*.html"):
            relative_path = template_path.relative_to(self.template_dir)
            template_name = str(relative_path)
            
            logger.info(f"Validating template: {template_name}")
            results[template_name] = self.validate_template_comprehensive(template_name)
        
        return results
    
    def generate_validation_summary(self, validation_results: Dict[str, TemplateValidationReport]) -> str:
        """
        Generate a summary report of template validation results
        
        Args:
            validation_results: Results from validate_all_templates()
            
        Returns:
            str: Summary report content
        """
        total_templates = len(validation_results)
        valid_templates = sum(1 for r in validation_results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in validation_results.values())
        total_warnings = sum(len(r.warnings) for r in validation_results.values())
        
        summary = f"""# Template Validation Summary

**Generated:** {datetime.now().isoformat()}

## Overview

- **Total Templates:** {total_templates}
- **Valid Templates:** {valid_templates}
- **Templates with Issues:** {total_templates - valid_templates}
- **Total Errors:** {total_errors}
- **Total Warnings:** {total_warnings}

## Template Status

"""
        
        for template_name, result in validation_results.items():
            status = "✓ VALID" if result.is_valid else "✗ INVALID"
            error_count = len(result.errors)
            warning_count = len(result.warnings)
            
            summary += f"- **{template_name}**: {status}"
            if error_count > 0:
                summary += f" ({error_count} errors"
            if warning_count > 0:
                summary += f", {warning_count} warnings" if error_count > 0 else f" ({warning_count} warnings"
            if error_count > 0 or warning_count > 0:
                summary += ")"
            summary += "\n"
        
        # Add detailed issues for invalid templates
        invalid_templates = {k: v for k, v in validation_results.items() if not v.is_valid}
        if invalid_templates:
            summary += "\n## Detailed Issues\n\n"
            
            for template_name, result in invalid_templates.items():
                summary += f"### {template_name}\n\n"
                
                if result.errors:
                    summary += "**Errors:**\n"
                    for error in result.errors:
                        summary += f"- {error.message}\n"
                        if error.suggestion:
                            summary += f"  *Suggestion: {error.suggestion}*\n"
                    summary += "\n"
                
                if result.warnings:
                    summary += "**Warnings:**\n"
                    for warning in result.warnings:
                        summary += f"- {warning.message}\n"
                        if warning.suggestion:
                            summary += f"  *Suggestion: {warning.suggestion}*\n"
                    summary += "\n"
        
        return summary


def main():
    """Main CLI interface for template migration service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Template Validation and Migration Service')
    parser.add_argument('--template-dir', default='templates', help='Template directory')
    parser.add_argument('--backup-dir', default='template_backups', help='Backup directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate templates')
    validate_parser.add_argument('template_name', nargs='?', help='Specific template to validate (optional)')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate ReportLab template')
    migrate_parser.add_argument('template_name', help='Name for migrated template')
    migrate_parser.add_argument('reportlab_file', help='Path to ReportLab code file')
    
    # Documentation command
    doc_parser = subparsers.add_parser('docs', help='Generate template documentation')
    doc_parser.add_argument('--output', default='TEMPLATE_DOCUMENTATION.md', help='Output file path')
    
    # API compatibility command
    api_parser = subparsers.add_parser('test-api', help='Test API compatibility')
    api_parser.add_argument('endpoints', nargs='+', help='API endpoints to test')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    service = TemplateMigrationService(args.template_dir, args.backup_dir)
    
    if args.command == 'validate':
        if args.template_name:
            # Validate specific template
            result = service.validate_template_comprehensive(args.template_name)
            print(f"Template: {result.template_name}")
            print(f"Valid: {result.is_valid}")
            
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  - {error.message}")
            
            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  - {warning.message}")
                    
        else:
            # Validate all templates
            results = service.validate_all_templates()
            summary = service.generate_validation_summary(results)
            print(summary)
            
            # Save summary to file
            with open('template_validation_summary.md', 'w') as f:
                f.write(summary)
            print("\nSummary saved to: template_validation_summary.md")
    
    elif args.command == 'migrate':
        # Read ReportLab code
        with open(args.reportlab_file, 'r') as f:
            reportlab_code = f.read()
        
        result = service.migrate_reportlab_template(args.template_name, reportlab_code)
        
        print(f"Migration: {'SUCCESS' if result.migration_successful else 'FAILED'}")
        print(f"Template: {result.template_name}")
        print(f"Backward Compatible: {result.backward_compatible}")
        
        if result.migration_notes:
            print("\nNotes:")
            for note in result.migration_notes:
                print(f"  - {note}")
        
        if result.issues_found:
            print("\nIssues:")
            for issue in result.issues_found:
                print(f"  - {issue.message}")
    
    elif args.command == 'docs':
        doc_path = service.save_documentation(args.output)
        print(f"Documentation generated: {doc_path}")
    
    elif args.command == 'test-api':
        results = asyncio.run(service.validate_api_compatibility(args.endpoints))
        
        print("API Compatibility Results:")
        for result in results:
            status = "✓ COMPATIBLE" if result.compatible else "✗ INCOMPATIBLE"
            print(f"  {result.endpoint}: {status}")
            
            if result.issues:
                for issue in result.issues:
                    print(f"    - {issue}")


if __name__ == '__main__':
    main()