"""
Property-based test for card validation.

This test validates Property 15: Card validation
Requirements: 5.6, 5.7

**Feature: platform-modernization, Property 15: Card validation**
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite


# Test configuration
DEFAULT_SETTINGS = settings(
    max_examples=100,
    deadline=30000,  # 30 seconds
    suppress_health_check=[
        HealthCheck.function_scoped_fixture
    ]
)


class CardValidator:
    """Card validation utility class for testing payment method validation"""
    
    SUPPORTED_CARD_TYPES = {
        'visa': {
            'prefixes': ['4'],
            'lengths': [13, 16, 19],
            'name': 'Visa'
        },
        'mastercard': {
            'prefixes': ['51', '52', '53', '54', '55', '2221', '2222', '2223', '2224', '2225', '2226', '2227', '2228', '2229', '223', '224', '225', '226', '227', '228', '229', '23', '24', '25', '26', '270', '271', '2720'],
            'lengths': [16],
            'name': 'Mastercard'
        },
        'amex': {
            'prefixes': ['34', '37'],
            'lengths': [15],
            'name': 'American Express'
        },
        'discover': {
            'prefixes': ['6011', '622126', '622127', '622128', '622129', '62213', '62214', '62215', '62216', '62217', '62218', '62219', '6222', '6223', '6224', '6225', '6226', '6227', '6228', '644', '645', '646', '647', '648', '649', '65'],
            'lengths': [16],
            'name': 'Discover'
        },
        'jcb': {
            'prefixes': ['3528', '3529', '353', '354', '355', '356', '357', '358'],
            'lengths': [16],
            'name': 'JCB'
        },
        'diners': {
            'prefixes': ['300', '301', '302', '303', '304', '305', '36', '38'],
            'lengths': [14],
            'name': 'Diners Club'
        }
    }
    
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """
        Validate card number using Luhn algorithm
        """
        if not card_number or not card_number.isdigit():
            return False
            
        # Remove any spaces or dashes
        card_number = re.sub(r'[^0-9]', '', card_number)
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False
            
        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
            
        return total % 10 == 0
    
    @classmethod
    def detect_card_type(cls, card_number: str) -> Optional[str]:
        """
        Detect card type based on card number
        """
        if not card_number:
            return None
            
        # Remove any spaces or dashes
        card_number = re.sub(r'[^0-9]', '', card_number)
        
        for card_type, info in cls.SUPPORTED_CARD_TYPES.items():
            for prefix in info['prefixes']:
                if card_number.startswith(prefix) and len(card_number) in info['lengths']:
                    return card_type
        
        return None
    
    @classmethod
    def validate_card_number(cls, card_number: str) -> Dict[str, Any]:
        """
        Comprehensive card number validation
        """
        result = {
            'valid': False,
            'card_type': None,
            'errors': []
        }
        
        if not card_number:
            result['errors'].append('Card number is required')
            return result
        
        # Remove spaces and dashes
        clean_number = re.sub(r'[^0-9]', '', card_number)
        
        # Check if it contains only digits
        if not clean_number.isdigit():
            result['errors'].append('Card number must contain only digits')
            return result
        
        # Check length
        if len(clean_number) < 13 or len(clean_number) > 19:
            result['errors'].append('Card number must be between 13 and 19 digits')
            return result
        
        # Detect card type
        card_type = cls.detect_card_type(clean_number)
        if not card_type:
            result['errors'].append('Unsupported card type')
            return result
        
        result['card_type'] = card_type
        
        # Validate using Luhn algorithm
        if not cls.luhn_check(clean_number):
            result['errors'].append('Invalid card number (failed checksum)')
            return result
        
        result['valid'] = True
        return result
    
    @staticmethod
    def validate_expiry_date(month: int, year: int) -> Dict[str, Any]:
        """
        Validate card expiry date
        """
        result = {
            'valid': False,
            'errors': []
        }
        
        # Validate month
        if not isinstance(month, int) or month < 1 or month > 12:
            result['errors'].append('Expiry month must be between 1 and 12')
            return result
        
        # Validate year
        current_year = datetime.now().year
        if not isinstance(year, int) or year < current_year or year > current_year + 20:
            result['errors'].append(f'Expiry year must be between {current_year} and {current_year + 20}')
            return result
        
        # Check if card is expired
        current_date = datetime.now()
        expiry_date = datetime(year, month, 1)
        
        # Add one month to get the last day of the expiry month
        if month == 12:
            expiry_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            expiry_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        if expiry_date < current_date:
            result['errors'].append('Card has expired')
            return result
        
        result['valid'] = True
        return result
    
    @staticmethod
    def validate_cvv(cvv: str, card_type: str = None) -> Dict[str, Any]:
        """
        Validate CVV/CVC code
        """
        result = {
            'valid': False,
            'errors': []
        }
        
        if not cvv:
            result['errors'].append('CVV is required')
            return result
        
        if not cvv.isdigit():
            result['errors'].append('CVV must contain only digits')
            return result
        
        # American Express uses 4-digit CVV, others use 3-digit
        expected_length = 4 if card_type == 'amex' else 3
        
        if len(cvv) != expected_length:
            result['errors'].append(f'CVV must be {expected_length} digits for {card_type or "this card type"}')
            return result
        
        result['valid'] = True
        return result


@composite
def valid_card_numbers(draw):
    """Generate valid card numbers for different card types"""
    card_type = draw(st.sampled_from(list(CardValidator.SUPPORTED_CARD_TYPES.keys())))
    card_info = CardValidator.SUPPORTED_CARD_TYPES[card_type]
    
    prefix = draw(st.sampled_from(card_info['prefixes']))
    length = draw(st.sampled_from(card_info['lengths']))
    
    # Generate remaining digits
    remaining_length = length - len(prefix) - 1  # -1 for check digit
    if remaining_length > 0:
        remaining_digits = draw(st.text(alphabet='0123456789', min_size=remaining_length, max_size=remaining_length))
    else:
        remaining_digits = ''
    
    # Calculate check digit using Luhn algorithm
    partial_number = prefix + remaining_digits
    total = 0
    for i, digit in enumerate(reversed(partial_number)):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n = n // 10 + n % 10
        total += n
    
    check_digit = (10 - (total % 10)) % 10
    full_number = partial_number + str(check_digit)
    
    return {
        'number': full_number,
        'type': card_type,
        'formatted': f"{full_number[:4]} {full_number[4:8]} {full_number[8:12]} {full_number[12:]}" if len(full_number) >= 16 else full_number
    }


@composite
def invalid_card_numbers(draw):
    """Generate invalid card numbers"""
    invalid_type = draw(st.sampled_from([
        'too_short',
        'too_long', 
        'invalid_luhn',
        'unsupported_prefix',
        'non_numeric'
    ]))
    
    if invalid_type == 'too_short':
        return draw(st.text(alphabet='0123456789', min_size=1, max_size=12))
    elif invalid_type == 'too_long':
        return draw(st.text(alphabet='0123456789', min_size=20, max_size=25))
    elif invalid_type == 'invalid_luhn':
        # Generate a number that fails Luhn check
        valid_card = draw(valid_card_numbers())
        number = valid_card['number']
        # Change last digit to make it invalid
        last_digit = int(number[-1])
        invalid_digit = (last_digit + 1) % 10
        return number[:-1] + str(invalid_digit)
    elif invalid_type == 'unsupported_prefix':
        # Use a prefix that's not supported
        return draw(st.text(alphabet='0123456789', min_size=16, max_size=16)).replace('4', '1').replace('5', '1').replace('3', '1').replace('6', '1')
    elif invalid_type == 'non_numeric':
        return draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=16, max_size=16))


@composite
def valid_expiry_dates(draw):
    """Generate valid expiry dates"""
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    year = draw(st.integers(min_value=current_year, max_value=current_year + 10))
    
    # If it's the current year, month must be current month or later
    if year == current_year:
        month = draw(st.integers(min_value=current_month, max_value=12))
    else:
        month = draw(st.integers(min_value=1, max_value=12))
    
    return {'month': month, 'year': year}


@composite
def invalid_expiry_dates(draw):
    """Generate invalid expiry dates"""
    invalid_type = draw(st.sampled_from(['expired', 'invalid_month', 'invalid_year', 'too_far_future']))
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if invalid_type == 'expired':
        if current_month == 1:
            return {'month': 12, 'year': current_year - 1}
        else:
            return {'month': current_month - 1, 'year': current_year}
    elif invalid_type == 'invalid_month':
        month = draw(st.sampled_from([0, 13, 14, -1]))
        year = draw(st.integers(min_value=current_year, max_value=current_year + 5))
        return {'month': month, 'year': year}
    elif invalid_type == 'invalid_year':
        month = draw(st.integers(min_value=1, max_value=12))
        year = draw(st.integers(min_value=1900, max_value=current_year - 1))
        return {'month': month, 'year': year}
    elif invalid_type == 'too_far_future':
        month = draw(st.integers(min_value=1, max_value=12))
        year = draw(st.integers(min_value=current_year + 21, max_value=current_year + 50))
        return {'month': month, 'year': year}


class TestCardValidationProperty:
    """Property-based tests for card validation"""

    @given(card_data=valid_card_numbers())
    @DEFAULT_SETTINGS
    def test_valid_card_numbers_property(self, card_data):
        """
        Property: For any valid card number, validation should succeed and detect correct card type
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6, 5.7**
        """
        card_number = card_data['number']
        expected_type = card_data['type']
        
        # Test card number validation
        result = CardValidator.validate_card_number(card_number)
        
        # Property: Valid card numbers should pass validation
        assert result['valid'] is True, f"Valid card number {card_number} should pass validation"
        assert len(result['errors']) == 0, f"Valid card number should have no errors, got: {result['errors']}"
        
        # Property: Card type should be detected correctly
        assert result['card_type'] == expected_type, f"Expected card type {expected_type}, got {result['card_type']}"
        
        # Property: Luhn check should pass for valid numbers
        assert CardValidator.luhn_check(card_number) is True, f"Valid card number {card_number} should pass Luhn check"
        
        # Property: Card type detection should be consistent
        detected_type = CardValidator.detect_card_type(card_number)
        assert detected_type == expected_type, f"Card type detection should be consistent"
        
        # Test with formatted number (spaces)
        formatted_result = CardValidator.validate_card_number(card_data['formatted'])
        assert formatted_result['valid'] is True, "Formatted card numbers should also be valid"
        assert formatted_result['card_type'] == expected_type, "Formatted numbers should detect same card type"

    @given(card_number=invalid_card_numbers())
    @DEFAULT_SETTINGS
    def test_invalid_card_numbers_property(self, card_number):
        """
        Property: For any invalid card number, validation should fail with appropriate error messages
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6, 5.7**
        """
        result = CardValidator.validate_card_number(card_number)
        
        # Property: Invalid card numbers should fail validation
        assert result['valid'] is False, f"Invalid card number {card_number} should fail validation"
        assert len(result['errors']) > 0, f"Invalid card number should have error messages"
        
        # Property: Error messages should be descriptive
        for error in result['errors']:
            assert isinstance(error, str), "Error messages should be strings"
            assert len(error) > 0, "Error messages should not be empty"

    @given(expiry_data=valid_expiry_dates())
    @DEFAULT_SETTINGS
    def test_valid_expiry_dates_property(self, expiry_data):
        """
        Property: For any valid expiry date, validation should succeed
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.7**
        """
        month = expiry_data['month']
        year = expiry_data['year']
        
        result = CardValidator.validate_expiry_date(month, year)
        
        # Property: Valid expiry dates should pass validation
        assert result['valid'] is True, f"Valid expiry date {month}/{year} should pass validation"
        assert len(result['errors']) == 0, f"Valid expiry date should have no errors, got: {result['errors']}"
        
        # Property: Month should be in valid range
        assert 1 <= month <= 12, f"Month should be between 1 and 12, got {month}"
        
        # Property: Year should be reasonable
        current_year = datetime.now().year
        assert current_year <= year <= current_year + 20, f"Year should be between {current_year} and {current_year + 20}, got {year}"

    @given(expiry_data=invalid_expiry_dates())
    @DEFAULT_SETTINGS
    def test_invalid_expiry_dates_property(self, expiry_data):
        """
        Property: For any invalid expiry date, validation should fail with appropriate error messages
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.7**
        """
        month = expiry_data['month']
        year = expiry_data['year']
        
        result = CardValidator.validate_expiry_date(month, year)
        
        # Property: Invalid expiry dates should fail validation
        assert result['valid'] is False, f"Invalid expiry date {month}/{year} should fail validation"
        assert len(result['errors']) > 0, f"Invalid expiry date should have error messages"
        
        # Property: Error messages should be descriptive
        for error in result['errors']:
            assert isinstance(error, str), "Error messages should be strings"
            assert len(error) > 0, "Error messages should not be empty"

    @given(
        cvv=st.text(alphabet='0123456789', min_size=3, max_size=4),
        card_type=st.sampled_from(['visa', 'mastercard', 'amex', 'discover'])
    )
    @DEFAULT_SETTINGS
    def test_valid_cvv_property(self, cvv, card_type):
        """
        Property: For any valid CVV, validation should succeed based on card type
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6**
        """
        # Skip invalid combinations
        if card_type == 'amex' and len(cvv) != 4:
            assume(False)
        if card_type != 'amex' and len(cvv) != 3:
            assume(False)
        
        result = CardValidator.validate_cvv(cvv, card_type)
        
        # Property: Valid CVV should pass validation
        assert result['valid'] is True, f"Valid CVV {cvv} for {card_type} should pass validation"
        assert len(result['errors']) == 0, f"Valid CVV should have no errors, got: {result['errors']}"

    @given(
        cvv=st.one_of(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5),  # Non-numeric
            st.text(alphabet='0123456789', min_size=1, max_size=2),  # Too short
            st.text(alphabet='0123456789', min_size=5, max_size=10),  # Too long
            st.just('')  # Empty
        ),
        card_type=st.sampled_from(['visa', 'mastercard', 'amex', 'discover'])
    )
    @DEFAULT_SETTINGS
    def test_invalid_cvv_property(self, cvv, card_type):
        """
        Property: For any invalid CVV, validation should fail with appropriate error messages
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6**
        """
        result = CardValidator.validate_cvv(cvv, card_type)
        
        # Property: Invalid CVV should fail validation
        assert result['valid'] is False, f"Invalid CVV {cvv} for {card_type} should fail validation"
        assert len(result['errors']) > 0, f"Invalid CVV should have error messages"
        
        # Property: Error messages should be descriptive
        for error in result['errors']:
            assert isinstance(error, str), "Error messages should be strings"
            assert len(error) > 0, "Error messages should not be empty"

    @given(card_data=valid_card_numbers())
    @DEFAULT_SETTINGS
    def test_supported_card_types_property(self, card_data):
        """
        Property: For any supported card type, the system should handle all major card brands
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6**
        """
        card_type = card_data['type']
        
        # Property: All major card types should be supported
        supported_types = set(CardValidator.SUPPORTED_CARD_TYPES.keys())
        major_types = {'visa', 'mastercard', 'amex', 'discover'}
        
        assert major_types.issubset(supported_types), f"All major card types should be supported. Missing: {major_types - supported_types}"
        
        # Property: Each card type should have proper configuration
        card_info = CardValidator.SUPPORTED_CARD_TYPES[card_type]
        assert 'prefixes' in card_info, f"Card type {card_type} should have prefixes defined"
        assert 'lengths' in card_info, f"Card type {card_type} should have lengths defined"
        assert 'name' in card_info, f"Card type {card_type} should have name defined"
        
        assert len(card_info['prefixes']) > 0, f"Card type {card_type} should have at least one prefix"
        assert len(card_info['lengths']) > 0, f"Card type {card_type} should have at least one valid length"
        assert len(card_info['name']) > 0, f"Card type {card_type} should have a non-empty name"

    @given(
        card_data=valid_card_numbers(),
        expiry_data=valid_expiry_dates()
    )
    @DEFAULT_SETTINGS
    def test_comprehensive_payment_method_validation_property(self, card_data, expiry_data):
        """
        Property: For any complete payment method data, comprehensive validation should work correctly
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6, 5.7**
        """
        card_number = card_data['number']
        card_type = card_data['type']
        month = expiry_data['month']
        year = expiry_data['year']
        cvv = '123' if card_type != 'amex' else '1234'
        
        # Validate each component
        card_result = CardValidator.validate_card_number(card_number)
        expiry_result = CardValidator.validate_expiry_date(month, year)
        cvv_result = CardValidator.validate_cvv(cvv, card_type)
        
        # Property: All components should be valid for a complete valid payment method
        assert card_result['valid'] is True, "Card number should be valid"
        assert expiry_result['valid'] is True, "Expiry date should be valid"
        assert cvv_result['valid'] is True, "CVV should be valid"
        
        # Property: Card type detection should be consistent across validations
        assert card_result['card_type'] == card_type, "Card type should be detected consistently"
        
        # Property: No validation errors should exist for valid data
        all_errors = card_result['errors'] + expiry_result['errors'] + cvv_result['errors']
        assert len(all_errors) == 0, f"No validation errors should exist for valid data, got: {all_errors}"

    @given(
        number_with_spaces=st.text(alphabet='0123456789 -', min_size=13, max_size=25)
    )
    @DEFAULT_SETTINGS
    def test_card_number_formatting_tolerance_property(self, number_with_spaces):
        """
        Property: For any card number with formatting (spaces, dashes), validation should handle it correctly
        **Feature: platform-modernization, Property 15: Card validation**
        **Validates: Requirements 5.6**
        """
        # Skip if no digits
        clean_number = re.sub(r'[^0-9]', '', number_with_spaces)
        assume(len(clean_number) >= 13)
        assume(len(clean_number) <= 19)
        
        # Test that formatting is handled consistently
        result_formatted = CardValidator.validate_card_number(number_with_spaces)
        result_clean = CardValidator.validate_card_number(clean_number)
        
        # Property: Formatting should not affect validation result
        assert result_formatted['valid'] == result_clean['valid'], "Formatting should not affect validation result"
        assert result_formatted['card_type'] == result_clean['card_type'], "Formatting should not affect card type detection"
        
        # Property: If one fails, both should fail with similar reasons
        if not result_formatted['valid']:
            assert not result_clean['valid'], "If formatted version fails, clean version should also fail"