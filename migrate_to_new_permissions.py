#!/usr/bin/env python3
"""
Script to migrate the entire codebase to use the new permission system directly.
This removes the dependency on the integration module and uses the new system exclusively.
"""

import os
import re
from pathlib import Path

def update_api_file(filepath):
    """Update a single API file to use new permission system directly"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace integration imports with direct imports from new system
    replacements = [
        # Replace integration imports with direct permission imports
        (
            r'from ctutor_backend\.permissions\.integration import \(\s*adaptive_check_permissions as check_permissions,?\s*([^)]*)\)',
            r'from ctutor_backend.permissions.core import check_permissions\nfrom ctutor_backend.permissions.principal import \1'
        ),
        (
            r'from ctutor_backend\.permissions\.integration import adaptive_check_permissions as check_permissions,?\s*',
            r'from ctutor_backend.permissions.core import check_permissions, '
        ),
        (
            r'from ctutor_backend\.permissions\.integration import \(\s*adaptive_check_course_permissions as check_course_permissions,?\s*([^)]*)\)',
            r'from ctutor_backend.permissions.core import check_course_permissions\nfrom ctutor_backend.permissions.principal import \1'
        ),
        (
            r'from ctutor_backend\.permissions\.integration import adaptive_check_course_permissions as check_course_permissions,?\s*',
            r'from ctutor_backend.permissions.core import check_course_permissions, '
        ),
        (
            r'from ctutor_backend\.permissions\.integration import \(\s*adaptive_check_admin as check_admin,?\s*([^)]*)\)',
            r'from ctutor_backend.permissions.core import check_admin\nfrom ctutor_backend.permissions.principal import \1'
        ),
        (
            r'from ctutor_backend\.permissions\.integration import adaptive_check_admin as check_admin,?\s*',
            r'from ctutor_backend.permissions.core import check_admin, '
        ),
        (
            r'from ctutor_backend\.permissions\.integration import \(\s*adaptive_get_permitted_course_ids as get_permitted_course_ids,?\s*([^)]*)\)',
            r'from ctutor_backend.permissions.core import get_permitted_course_ids\nfrom ctutor_backend.permissions.principal import \1'
        ),
        (
            r'from ctutor_backend\.permissions\.integration import adaptive_get_permitted_course_ids as get_permitted_course_ids,?\s*',
            r'from ctutor_backend.permissions.core import get_permitted_course_ids, '
        ),
        # Replace Principal import from integration
        (
            r'from ctutor_backend\.permissions\.integration import ([^,\n]*,\s*)?Principal',
            r'from ctutor_backend.permissions.core import \1\nfrom ctutor_backend.permissions.principal import Principal'
        ),
        # Replace db_get_claims and db_get_course_claims
        (
            r'from ctutor_backend\.permissions\.integration import ([^,\n]*,\s*)?(db_get_claims|db_get_course_claims)',
            r'from ctutor_backend.permissions.core import \1\2'
        ),
        # Clean up any remaining integration imports
        (
            r'from ctutor_backend\.permissions\.integration import\s*\n',
            ''
        ),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Clean up duplicate imports and empty lines
    lines = content.split('\n')
    seen_imports = set()
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        # Skip duplicate imports
        if line.startswith('from ctutor_backend.permissions'):
            if line in seen_imports:
                continue
            seen_imports.add(line)
        
        # Skip multiple empty lines
        if line.strip() == '':
            if prev_empty:
                continue
            prev_empty = True
        else:
            prev_empty = False
        
        cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # Consolidate imports from same module
    content = consolidate_imports(content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    
    return False


def consolidate_imports(content):
    """Consolidate multiple imports from the same module into one line"""
    
    lines = content.split('\n')
    import_dict = {}
    new_lines = []
    
    for line in lines:
        # Check if it's an import from permissions modules
        match = re.match(r'from (ctutor_backend\.permissions\.\w+) import (.+)', line)
        if match:
            module = match.group(1)
            imports = match.group(2).strip()
            
            if module not in import_dict:
                import_dict[module] = []
            
            # Parse imports (handle both single and multiple)
            if ',' in imports:
                items = [item.strip() for item in imports.split(',')]
            else:
                items = [imports.strip()]
            
            for item in items:
                if item and item not in import_dict[module]:
                    import_dict[module].append(item)
        else:
            # If we have accumulated imports, add them before this line
            if import_dict and not line.startswith('from ctutor_backend.permissions'):
                for module, items in sorted(import_dict.items()):
                    if items:
                        if len(items) == 1:
                            new_lines.append(f"from {module} import {items[0]}")
                        else:
                            new_lines.append(f"from {module} import {', '.join(sorted(set(items)))}")
                import_dict.clear()
            
            new_lines.append(line)
    
    # Add any remaining imports at the end
    for module, items in sorted(import_dict.items()):
        if items:
            if len(items) == 1:
                new_lines.append(f"from {module} import {items[0]}")
            else:
                new_lines.append(f"from {module} import {', '.join(sorted(set(items)))}")
    
    return '\n'.join(new_lines)


def update_auth_file():
    """Special handling for auth.py file"""
    filepath = Path('/home/theta/computor/computor-fullstack/src/ctutor_backend/api/auth.py')
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # auth.py should import from core, not integration
    content = re.sub(
        r'from ctutor_backend\.permissions\.integration import.*\n',
        '',
        content
    )
    
    # Add necessary imports from core if not present
    if 'from ctutor_backend.permissions.core import' not in content:
        # Add after other imports
        import_line = 'from ctutor_backend.permissions.core import db_get_claims, db_get_course_claims\n'
        # Find a good place to insert (after other ctutor_backend imports)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from ctutor_backend.interface'):
                lines.insert(i, import_line)
                break
        content = '\n'.join(lines)
    
    # Also need Principal and build_claim_actions
    if 'from ctutor_backend.permissions.principal import' not in content:
        if 'from ctutor_backend.interface.permissions import' in content:
            content = content.replace(
                'from ctutor_backend.interface.permissions import Principal, build_claim_actions',
                'from ctutor_backend.permissions.principal import Principal, build_claim_actions'
            )
    
    with open(filepath, 'w') as f:
        f.write(content)


def main():
    """Update all API files to use new permission system directly"""
    
    api_files = [
        'crud.py',
        'course_contents.py',
        'organizations.py',
        'system.py',
        'results.py',
        'tests.py',
        'students.py',
        'tutor.py',
        'lecturer.py',
        'course_members.py',
        'user_roles.py',
        'role_claims.py',
        'courses.py',
        'course_execution_backend.py',
    ]
    
    api_dir = Path('/home/theta/computor/computor-fullstack/src/ctutor_backend/api')
    
    print("Migrating to new permission system...")
    print("=" * 60)
    
    # First, update auth.py specially
    print("Updating auth.py...")
    update_auth_file()
    
    # Then update all other API files
    updated_count = 0
    for filename in api_files:
        filepath = api_dir / filename
        if filepath.exists():
            if update_api_file(filepath):
                print(f"✅ Updated: {filename}")
                updated_count += 1
            else:
                print(f"⏭️  Already migrated: {filename}")
        else:
            print(f"❌ File not found: {filename}")
    
    print("=" * 60)
    print(f"Updated {updated_count} files")
    
    # Update the integration module to default to NEW system
    integration_file = Path('/home/theta/computor/computor-fullstack/src/ctutor_backend/permissions/integration.py')
    if integration_file.exists():
        with open(integration_file, 'r') as f:
            content = f.read()
        
        # Change default to true
        content = re.sub(
            r'USE_NEW_PERMISSION_SYSTEM = os\.getenv\("USE_NEW_PERMISSION_SYSTEM", "false"\)\.lower\(\) == "true"',
            r'USE_NEW_PERMISSION_SYSTEM = os.getenv("USE_NEW_PERMISSION_SYSTEM", "true").lower() == "true"',
            content
        )
        
        with open(integration_file, 'w') as f:
            f.write(content)
        print("✅ Updated integration.py to default to NEW system")
    
    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("1. Run tests to verify everything works")
    print("2. The system now uses the new permission system by default")
    print("3. You can still switch back with USE_NEW_PERMISSION_SYSTEM=false if needed")


if __name__ == "__main__":
    main()