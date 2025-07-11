#!/usr/bin/env python3
"""
Test script to validate the color refactoring from enum to string.
"""

import os
import sys
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
# Add parent directory to path for ctutor_backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_color_validation():
    """Test the color validation functions."""
    print("🎨 Testing color validation functions...")
    
    try:
        from ctutor_backend.utils.color_validation import (
            is_valid_color, validate_color, is_valid_hex_color, 
            is_valid_rgb_color, is_valid_hsl_color, is_valid_css_named_color,
            get_color_examples
        )
        
        # Test valid colors
        valid_colors = [
            # Hex colors
            '#FF5733', '#ff5733', '#123', '#123456', '#12345678',
            # RGB/RGBA
            'rgb(255, 87, 51)', 'rgba(255, 87, 51, 0.8)',
            # HSL/HSLA
            'hsl(9, 100%, 60%)', 'hsla(9, 100%, 60%, 0.8)',
            # Named colors
            'red', 'blue', 'green', 'tomato', 'lightblue', 'darkslategray',
            # Tailwind colors
            'amber', 'emerald', 'sky', 'rose'
        ]
        
        invalid_colors = [
            'invalid-color', '#GGG', 'rgb(300, 300, 300)', 'hsl(400, 150%, 150%)',
            '', None, 123, 'rgb(255, 255)', 'rgba(255, 255, 255, 2.0)'
        ]
        
        print("   Testing valid colors:")
        for color in valid_colors:
            if is_valid_color(color):
                normalized = validate_color(color)
                print(f"   ✅ {color} -> {normalized}")
            else:
                print(f"   ❌ {color} (should be valid)")
                return False
        
        print("   Testing invalid colors:")
        for color in invalid_colors:
            if not is_valid_color(color):
                print(f"   ✅ {color} (correctly rejected)")
            else:
                print(f"   ❌ {color} (should be invalid)")
                return False
        
        print("✅ Color validation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Color validation test error: {e}")
        return False

def test_pydantic_interfaces():
    """Test that Pydantic interfaces accept valid colors and reject invalid ones."""
    print("\n🔧 Testing Pydantic interfaces with color validation...")
    
    try:
        from ctutor_backend.interface.course_content_types import (
            CourseContentTypeCreate, CourseContentTypeUpdate
        )
        
        # Test valid color creation
        valid_data = {
            'slug': 'test-assignment',
            'title': 'Test Assignment',
            'description': 'A test assignment',
            'color': '#FF5733',
            'course_id': 'test-course-id',
            'course_content_kind_id': 'assignment'
        }
        
        try:
            content_type = CourseContentTypeCreate(**valid_data)
            print(f"   ✅ Valid color accepted: {content_type.color}")
        except Exception as e:
            print(f"   ❌ Valid color rejected: {e}")
            return False
        
        # Test different valid color formats
        valid_colors = ['red', 'rgb(255, 0, 0)', 'hsl(0, 100%, 50%)', '#FF0000']
        for color in valid_colors:
            try:
                valid_data['color'] = color
                content_type = CourseContentTypeCreate(**valid_data)
                print(f"   ✅ {color} -> {content_type.color}")
            except Exception as e:
                print(f"   ❌ {color} rejected: {e}")
                return False
        
        # Test invalid color rejection
        invalid_colors = ['invalid-color', '#GGG', 'rgb(300, 300, 300)']
        for color in invalid_colors:
            try:
                valid_data['color'] = color
                content_type = CourseContentTypeCreate(**valid_data)
                print(f"   ❌ {color} should have been rejected")
                return False
            except Exception as e:
                print(f"   ✅ {color} correctly rejected: {e}")
        
        # Test update interface
        try:
            update_data = {'color': '#00FF00'}
            content_update = CourseContentTypeUpdate(**update_data)
            print(f"   ✅ Update with valid color: {content_update.color}")
        except Exception as e:
            print(f"   ❌ Update with valid color failed: {e}")
            return False
        
        print("✅ Pydantic interface tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Pydantic interface test error: {e}")
        return False

def test_model_import():
    """Test that the SQLAlchemy model imports correctly with String type."""
    print("\n🗃️ Testing SQLAlchemy model...")
    
    try:
        from ctutor_backend.model.sqlalchemy_models.course import CourseContentType
        
        # Check that the color column is a String type
        color_column = CourseContentType.__table__.columns.get('color')
        if color_column is not None:
            column_type = str(color_column.type)
            if 'VARCHAR' in column_type or 'String' in column_type:
                print(f"   ✅ Color column type: {column_type}")
            else:
                print(f"   ❌ Color column type is not String: {column_type}")
                return False
        else:
            print("   ❌ Color column not found in CourseContentType model")
            return False
        
        print("✅ SQLAlchemy model test passed")
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy model test error: {e}")
        return False

def test_migration_file():
    """Test that the migration file exists and has correct content."""
    print("\n🔄 Testing migration file...")
    
    try:
        migration_path = "/home/theta/computingtutor/computor-fullstack/src/ctutor_backend/alembic/versions/27db3ea1442c_refactor_ctutor_color_to_string.py"
        
        if os.path.exists(migration_path):
            print(f"   ✅ Migration file exists: {migration_path}")
            
            with open(migration_path, 'r') as f:
                content = f.read()
                
            if 'VARCHAR(255)' in content or 'String(255)' in content:
                print("   ✅ Migration contains VARCHAR/String conversion")
            else:
                print("   ❌ Migration does not contain VARCHAR/String conversion")
                return False
                
            if 'DROP TYPE IF EXISTS ctutor_color CASCADE' in content:
                print("   ✅ Migration drops ctutor_color enum")
            else:
                print("   ❌ Migration does not drop ctutor_color enum")
                return False
                
        else:
            print(f"   ❌ Migration file not found: {migration_path}")
            return False
        
        print("✅ Migration file test passed")
        return True
        
    except Exception as e:
        print(f"❌ Migration file test error: {e}")
        return False

def display_color_examples():
    """Display examples of valid colors."""
    print("\n🎨 Examples of valid colors:")
    
    try:
        from ctutor_backend.utils.color_validation import get_color_examples
        
        examples = get_color_examples()
        for example in examples:
            print(f"   • {example}")
        
        print("\n📚 Color format documentation:")
        print("   • Hex: #RGB, #RRGGBB, #RGBA, #RRGGBBAA")
        print("   • RGB: rgb(r, g, b), rgba(r, g, b, a)")
        print("   • HSL: hsl(h, s%, l%), hsla(h, s%, l%, a)")
        print("   • Named: red, blue, green, tomato, lightblue, etc.")
        print("   • Tailwind: amber, emerald, sky, rose, etc.")
        
    except Exception as e:
        print(f"❌ Could not display examples: {e}")

def main():
    """Run all color refactoring tests."""
    print("🎨 Color Refactoring Test Suite")
    print("=" * 50)
    
    tests = [
        test_color_validation,
        test_pydantic_interfaces,
        test_model_import,
        test_migration_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    display_color_examples()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All color refactoring tests passed!")
        print("✅ ctutor_color successfully refactored from ENUM to String with validation")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)