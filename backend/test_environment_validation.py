#!/usr/bin/env python3
"""
Test script for environment validation functionality
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_container_environment_service():
    """Test ContainerEnvironmentService functionality"""
    print("Testing ContainerEnvironmentService...")
    
    # Load .env file first
    from dotenv import load_dotenv
    load_dotenv(".env")
    
    from core.container_environment import ContainerEnvironmentService, ValidationResult
    
    # Test validation with current environment
    result = ContainerEnvironmentService.validate_environment_variables(
        ["POSTGRES_USER", "POSTGRES_PASSWORD", "SECRET_KEY"], 
        "backend"
    )
    
    print(f"Validation result: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
    if result.warnings:
        print(f"Warnings: {len(result.warnings)}")
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    return result.is_valid


def test_environment_validator():
    """Test EnvironmentValidator functionality"""
    print("\nTesting EnvironmentValidator...")
    
    from core.environment_validator import EnvironmentValidator
    
    validator = EnvironmentValidator()
    print(f"Detected container: {validator.context.container_name}")
    print(f"Docker environment: {validator.context.is_docker}")
    print(f"Production mode: {validator.context.is_production}")
    print(f"Development mode: {validator.context.is_development}")
    
    # Test validation
    result = validator.validate_startup_environment()
    print(f"Startup validation: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
    
    return result.is_valid


def test_documentation_generation():
    """Test documentation generation"""
    print("\nTesting documentation generation...")
    
    try:
        from core.container_environment import ContainerEnvironmentService, load_and_validate_all_containers
        
        containers = load_and_validate_all_containers()
        documentation = ContainerEnvironmentService.generate_env_documentation(containers)
        
        print(f"Documentation generated: {len(documentation)} characters")
        print("✅ Documentation generation PASS")
        return True
        
    except Exception as e:
        print(f"❌ Documentation generation FAIL: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ENVIRONMENT VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        test_container_environment_service,
        test_environment_validator,
        test_documentation_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)