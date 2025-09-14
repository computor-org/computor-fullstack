"""
CLI commands for deployment operations.

This module provides commands for working with ComputorDeploymentConfig,
including generating example configurations and deploying hierarchies.
"""

import sys
import io
import os
import base64
import zipfile
import yaml
import click
from pathlib import Path

from ..interface.deployments_refactored import (
    ComputorDeploymentConfig,
    HierarchicalOrganizationConfig,
    HierarchicalCourseFamilyConfig,
    HierarchicalCourseConfig,
    GitLabConfig,
    ExecutionBackendConfig,
    ExecutionBackendReference,
    CourseProjects,
    CourseContentConfig,
    EXAMPLE_DEPLOYMENT,
    EXAMPLE_MULTI_DEPLOYMENT
)
from .auth import authenticate, get_crud_client, get_custom_client
from .config import CLIAuthConfig
from ..client.crud_client import CustomClient
from ..interface.users import UserCreate, UserInterface, UserQuery
from ..interface.accounts import AccountCreate, AccountInterface, AccountQuery
from ..interface.courses import CourseInterface, CourseQuery
from ..interface.course_members import CourseMemberCreate, CourseMemberInterface, CourseMemberQuery
from ..interface.course_groups import CourseGroupInterface, CourseGroupQuery, CourseGroupCreate
from ..interface.organizations import OrganizationInterface, OrganizationQuery
from ..interface.course_families import CourseFamilyInterface, CourseFamilyQuery
from ..interface.execution_backends import ExecutionBackendCreate, ExecutionBackendInterface, ExecutionBackendQuery, ExecutionBackendUpdate
from ..interface.course_execution_backends import CourseExecutionBackendCreate, CourseExecutionBackendInterface, CourseExecutionBackendQuery
from ..interface.roles import RoleInterface, RoleQuery
from ..interface.user_roles import UserRoleCreate, UserRoleInterface, UserRoleQuery
from ..interface.example import (
    ExampleRepositoryInterface,
    ExampleRepositoryCreate,
    ExampleRepositoryQuery,
    ExampleInterface,
    ExampleQuery,
)
from ..interface.course_contents import CourseContentCreate, CourseContentInterface, CourseContentQuery
from ..interface.course_content_types import CourseContentTypeInterface, CourseContentTypeQuery
from ..interface.course_content_kind import CourseContentKindInterface, CourseContentKindQuery
# Deployment is handled through course-contents API, not a separate deployment endpoint


@click.group()
def deployment():
    """Manage deployment configurations and operations."""
    pass


@deployment.command()
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='deployment.yaml',
    help='Output file path for the example deployment configuration'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['minimal', 'full', 'tutorial']),
    default='tutorial',
    help='Type of example to generate'
)
def init(output: str, format: str):
    """
    Generate an example deployment configuration file.
    
    This creates a template YAML file that can be customized for your deployment.
    """
    click.echo(f"Generating {format} deployment configuration...")
    
    if format == 'minimal':
        # Minimal configuration with only required fields
        config = ComputorDeploymentConfig(
            organizations=[
                HierarchicalOrganizationConfig(
                    name="My Organization",
                    path="my-org",
                    course_families=[
                        HierarchicalCourseFamilyConfig(
                            name="My Courses",
                            path="my-courses",
                            courses=[
                                HierarchicalCourseConfig(
                                    name="My First Course",
                                    path="course-2025"
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    elif format == 'full':
        # Use the multi-organization example
        config = EXAMPLE_MULTI_DEPLOYMENT
    else:  # tutorial
        # Use the example from deployments_refactored.py
        config = EXAMPLE_DEPLOYMENT
    
    # Write to file
    output_path = Path(output)
    yaml_content = config.get_deployment()
    
    # Add helpful comments to the YAML
    header_comments = """# Computor Deployment Configuration
# This file defines the organization -> course family -> course hierarchy
# 
# Environment variables can be used with ${VAR_NAME} or ${VAR_NAME:-default}
# 
# Required fields:
#   - organization.name, organization.path
#   - course_family.name, course_family.path  
#   - course.name, course.path
#
# Optional: GitLab configuration, execution backends, settings
#
"""
    
    with open(output_path, 'w') as f:
        f.write(header_comments)
        f.write(yaml_content)
    
    click.echo(f"✅ Created deployment configuration: {output_path}")
    click.echo(f"\nNext steps:")
    click.echo(f"1. Edit {output_path} to customize your deployment")
    click.echo(f"2. Set required environment variables (e.g., GITLAB_TOKEN)")
    click.echo(f"3. Run: ctutor deployment apply {output_path}")


def _deploy_users(config: ComputorDeploymentConfig, auth: CLIAuthConfig):
    """Deploy users and their course memberships from configuration."""
    
    # Get API clients
    user_client = get_crud_client(auth, UserInterface)
    account_client = get_crud_client(auth, AccountInterface)
    course_client = get_crud_client(auth, CourseInterface)
    course_member_client = get_crud_client(auth, CourseMemberInterface)
    course_group_client = get_crud_client(auth, CourseGroupInterface)
    org_client = get_crud_client(auth, OrganizationInterface)
    family_client = get_crud_client(auth, CourseFamilyInterface)
    
    processed_users = []
    failed_users = []
    
    for user_deployment in config.users:
        user_dep = user_deployment.user
        click.echo(f"\n👤 Processing: {user_dep.display_name} ({user_dep.username})")
        
        try:
            # Check if user already exists by email or username
            existing_users = []
            if user_dep.email:
                existing_users.extend(user_client.list(UserQuery(email=user_dep.email)))
            
            # Also check by username if not found by email
            if not existing_users and user_dep.username:
                existing_users.extend(user_client.list(UserQuery(username=user_dep.username)))
            
            if existing_users:
                user = existing_users[0]
                click.echo(f"  ℹ️  User already exists: {user.display_name}")
            else:
                # Create new user
                user_create = UserCreate(
                    given_name=user_dep.given_name,
                    family_name=user_dep.family_name,
                    email=user_dep.email,
                    number=user_dep.number,
                    username=user_dep.username,
                    user_type=user_dep.user_type,
                    properties=user_dep.properties
                )
                
                user = user_client.create(user_create)
                click.echo(f"  ✅ Created user: {user.display_name}")
                
            # Assign system roles if provided
            if user_dep.roles:
                role_client = get_crud_client(auth, RoleInterface)
                user_role_client = get_crud_client(auth, UserRoleInterface)
                
                for role_id in user_dep.roles:
                    try:
                        # Check if role exists
                        roles = role_client.list(RoleQuery(id=role_id))
                        if not roles:
                            click.echo(f"  ⚠️  Role not found: {role_id}")
                            continue
                        
                        # Check if user already has this role
                        existing_user_roles = user_role_client.list(UserRoleQuery(
                            user_id=str(user.id),
                            role_id=role_id
                        ))
                        
                        if existing_user_roles:
                            click.echo(f"  ℹ️  User already has role: {role_id}")
                        else:
                            # Assign role to user
                            user_role_create = UserRoleCreate(
                                user_id=str(user.id),
                                role_id=role_id
                            )
                            user_role_client.create(user_role_create)
                            click.echo(f"  ✅ Assigned role: {role_id}")
                    except Exception as e:
                        click.echo(f"  ⚠️  Failed to assign role {role_id}: {e}")
                
            # Set password if provided
            if user_dep.password:
                try:
                    # Use get_custom_client to get the authenticated client
                    client = get_custom_client(auth)
                    
                    password_payload = {
                        "username": user_dep.username,
                        "password": user_dep.password
                    }
                    client.create("/user/password", password_payload)
                    click.echo(f"  ✅ Set password for user: {user.display_name}")
                except Exception as e:
                    click.echo(f"  ⚠️  Failed to set password: {e}")
            
            # Create accounts
            for account_dep in user_deployment.accounts:
                # Check if account already exists for this user
                existing_accounts = account_client.list(AccountQuery(
                    provider_account_id=account_dep.provider_account_id,
                    user_id=str(user.id)
                ))
                
                if existing_accounts:
                    click.echo(f"  Account already exists: {account_dep.type} @ {account_dep.provider}")
                else:
                    # Create new account
                    account_create = AccountCreate(
                        provider=account_dep.provider,
                        type=account_dep.type,
                        provider_account_id=account_dep.provider_account_id,
                        user_id=str(user.id),
                        properties=account_dep.properties or {}
                    )
                    
                    account_client.create(account_create)
                    click.echo(f"  ✅ Created account: {account_dep.type} @ {account_dep.provider}")
            
            # Create course memberships
            for cm_dep in user_deployment.course_members:
                try:
                    course = None
                    
                    # Resolve course by path or ID
                    if cm_dep.is_path_based:
                        # Find organization
                        orgs = org_client.list(OrganizationQuery(path=cm_dep.organization))
                        if not orgs:
                            click.echo(f"  ⚠️  Organization not found: {cm_dep.organization}")
                            continue
                        org = orgs[0]
                        
                        # Find course family
                        families = family_client.list(CourseFamilyQuery(
                            organization_id=str(org.id),
                            path=cm_dep.course_family
                        ))
                        if not families:
                            click.echo(f"  ⚠️  Course family not found: {cm_dep.course_family}")
                            continue
                        family = families[0]
                        
                        # Find course
                        courses = course_client.list(CourseQuery(
                            course_family_id=str(family.id),
                            path=cm_dep.course
                        ))
                        if not courses:
                            click.echo(f"  ⚠️  Course not found: {cm_dep.course}")
                            continue
                        course = courses[0]
                    
                    elif cm_dep.is_id_based:
                        # Direct course lookup by ID
                        course = course_client.get(cm_dep.id)
                        if not course:
                            click.echo(f"  ⚠️  Course not found: {cm_dep.id}")
                            continue
                    
                    if course:
                        # Handle course group for students
                        course_group_id = None
                        if cm_dep.role == "_student" and cm_dep.group:
                            # Find or create course group
                            groups = course_group_client.list(CourseGroupQuery(
                                course_id=str(course.id),
                                title=cm_dep.group
                            ))
                            if groups:
                                course_group_id = str(groups[0].id)
                                click.echo(f"  Using existing group: {cm_dep.group}")
                            else:
                                # Create the course group
                                try:
                                    group_create = CourseGroupCreate(
                                        title=cm_dep.group,
                                        description=f"Course group {cm_dep.group}",
                                        course_id=str(course.id)
                                    )
                                    new_group = course_group_client.create(group_create)
                                    course_group_id = str(new_group.id)
                                    click.echo(f"  ✅ Created course group: {cm_dep.group}")
                                except Exception as e:
                                    click.echo(f"  ⚠️  Failed to create course group {cm_dep.group}: {e}")
                                    continue
                        
                        # Check if course member already exists
                        existing_members = course_member_client.list(CourseMemberQuery(
                            user_id=str(user.id),
                            course_id=str(course.id)
                        ))
                        
                        if existing_members:
                            existing_member = existing_members[0]
                            # Check if we need to update role or group
                            needs_update = False
                            if existing_member.course_role_id != cm_dep.role:
                                click.echo(f"  Updating role from {existing_member.course_role_id} to {cm_dep.role}")
                                needs_update = True
                            if course_group_id and existing_member.course_group_id != course_group_id:
                                click.echo(f"  Updating group assignment")
                                needs_update = True
                            
                            if needs_update:
                                # Update existing member
                                member_update = {
                                    'course_role_id': cm_dep.role,
                                    'course_group_id': course_group_id
                                }
                                course_member_client.update(str(existing_member.id), member_update)
                                click.echo(f"  ✅ Updated course membership: {course.path} as {cm_dep.role}")
                            else:
                                click.echo(f"  Already member of course: {course.path} as {cm_dep.role}")
                        else:
                            # Create new course member
                            member_create = CourseMemberCreate(
                                user_id=str(user.id),
                                course_id=str(course.id),
                                course_role_id=cm_dep.role,
                                course_group_id=course_group_id
                            )
                            
                            course_member_client.create(member_create)
                            click.echo(f"  ✅ Added to course: {course.path} as {cm_dep.role}")
                        
                except Exception as e:
                    click.echo(f"  ⚠️  Failed to add course membership: {e}")
            
            processed_users.append(user_dep)
            
        except Exception as e:
            click.echo(f"  ❌ Failed to process user: {e}")
            failed_users.append(user_dep)
    
    # Summary
    click.echo(f"\n📊 User Deployment Summary:")
    click.echo(f"  ✅ Successfully processed: {len(processed_users)} users")
    if failed_users:
        click.echo(f"  ❌ Failed: {len(failed_users)} users")
        for user_dep in failed_users:
            click.echo(f"    - {user_dep.display_name}")


def _deploy_execution_backends(config: ComputorDeploymentConfig, auth: CLIAuthConfig):
    """Deploy execution backends from configuration."""
    
    if not config.execution_backends:
        return
    
    click.echo(f"\n⚙️  Deploying {len(config.execution_backends)} execution backends...")
    
    # Get API client
    backend_client = get_crud_client(auth, ExecutionBackendInterface)
    
    for backend_config in config.execution_backends:
        click.echo(f"\n  Processing backend: {backend_config.slug}")
        
        try:
            # Check if backend already exists
            existing_backends = backend_client.list(ExecutionBackendQuery(slug=backend_config.slug))
            
            if existing_backends:
                backend = existing_backends[0]
                click.echo(f"    ℹ️  Backend already exists: {backend.slug}")
                
                # Check if we need to update properties
                if backend.type != backend_config.type or backend.properties != backend_config.properties:
                    # Update backend
                    backend_update = ExecutionBackendUpdate(
                        type=backend_config.type,
                        properties=backend_config.properties or {}
                    )

                    backend_client.update(str(backend.id), backend_update)
                    click.echo(f"    ✅ Updated backend: {backend_config.slug}")
            else:
                # Create new backend
                backend_create = ExecutionBackendCreate(
                    slug=backend_config.slug,
                    type=backend_config.type,
                    properties=backend_config.properties or {}
                )
                backend = backend_client.create(backend_create)
                click.echo(f"    ✅ Created backend: {backend_config.slug}")
                
        except Exception as e:
            click.echo(f"    ❌ Failed to deploy backend {backend_config.slug}: {e}")


def _deploy_course_contents(course_id: str, course_config: HierarchicalCourseConfig, auth: CLIAuthConfig, parent_path: str = None, position_counter: list = None):
    """Deploy course contents for a course."""
    
    if not course_config.contents:
        return
    
    # Initialize position counter if not provided
    if position_counter is None:
        position_counter = [1.0]
    
    # Get API clients
    content_client = get_crud_client(auth, CourseContentInterface)
    content_type_client = get_crud_client(auth, CourseContentTypeInterface)
    content_kind_client = get_crud_client(auth, CourseContentKindInterface)
    example_client = get_crud_client(auth, ExampleInterface)
    backend_client = get_crud_client(auth, ExecutionBackendInterface)
    custom_client = get_custom_client(auth)
    
    for content_config in course_config.contents:
        try:
            # Build the full path
            if parent_path:
                full_path = f"{parent_path}.{content_config.path}"
            else:
                full_path = content_config.path
            
            # Find the content type
            content_types = content_type_client.list(CourseContentTypeQuery(
                course_id=course_id,
                slug=content_config.content_type
            ))
            
            if not content_types:
                click.echo(f"    ⚠️  Content type not found: {content_config.content_type}")
                continue
            
            content_type = content_types[0]
            
            # Check if content already exists
            existing_contents = content_client.list(CourseContentQuery(
                course_id=course_id,
                path=full_path
            ))
            
            if existing_contents:
                content = existing_contents[0]
                click.echo(f"    ℹ️  Content already exists: {content.title} ({full_path})")
            else:
                # Determine position
                position = content_config.position if content_config.position is not None else position_counter[0]
                position_counter[0] += 1.0
                
                # Determine execution backend ID
                execution_backend_id = None
                if content_config.execution_backend:
                    backends = backend_client.list(ExecutionBackendQuery(slug=content_config.execution_backend))
                    if backends:
                        execution_backend_id = str(backends[0].id)
                
                # Create the content
                content_create = CourseContentCreate(
                    title=content_config.title,
                    description=content_config.description,
                    path=full_path,
                    course_id=course_id,
                    course_content_type_id=str(content_type.id),
                    position=position,
                    max_group_size=content_config.max_group_size,
                    max_test_runs=content_config.max_test_runs,
                    max_submissions=content_config.max_submissions,
                    execution_backend_id=execution_backend_id,
                    properties=content_config.properties
                )
                
                content = content_client.create(content_create)
                click.echo(f"    ✅ Created content: {content_config.title} ({full_path})")
            
            # Check if the content type is submittable by looking up its kind
            is_submittable = False
            if content_type.course_content_kind_id:
                content_kinds = content_kind_client.list(CourseContentKindQuery(
                    id=content_type.course_content_kind_id
                ))
                if content_kinds and len(content_kinds) > 0:
                    is_submittable = content_kinds[0].submittable
            
            # Handle example deployment for submittable content
            if is_submittable and content_config.example_identifier:
                # Find the example
                examples = example_client.list(ExampleQuery(
                    identifier=content_config.example_identifier
                ))
                
                if not examples:
                    click.echo(f"      ⚠️  Example not found: {content_config.example_identifier}")
                else:
                    example = examples[0]
                    
                    # Find the version using the API
                    version_tag = content_config.example_version_tag or "latest"
                    
                    # Get all versions for this example through the API
                    try:
                        versions_response = custom_client.get(f"examples/{example.id}/versions")
                        all_versions = versions_response if isinstance(versions_response, list) else []
                    except Exception:
                        all_versions = []
                    
                    # Find the matching version
                    version = None
                    if version_tag == "latest" and all_versions:
                        # Get the latest version (should already be sorted by version_number desc)
                        version = all_versions[0]
                    else:
                        # Look for specific version tag
                        for v in all_versions:
                            if v.get('version_tag') == version_tag:
                                version = v
                                break
                    
                    if version:
                        # Check if deployment already exists using the course-contents API
                        try:
                            deployment_info = custom_client.get(f"course-contents/deployment/{content.id}")
                            has_deployment = deployment_info and deployment_info.get('deployment_status') not in [None, 'unassigned']
                        except Exception:
                            has_deployment = False
                        
                        if has_deployment:
                            click.echo(f"      ℹ️  Deployment already exists for example: {content_config.example_identifier}")
                        else:
                            # Assign example using the course-contents API
                            try:
                                assign_payload = {
                                    "example_version_id": str(version['id'])
                                }
                                custom_client.create(f"course-contents/{content.id}/assign-example", assign_payload)
                                click.echo(f"      ✅ Assigned example: {content_config.example_identifier} ({version_tag})")
                            except Exception as e:
                                click.echo(f"      ⚠️  Failed to assign example: {e}")
                    else:
                        click.echo(f"      ⚠️  Example version not found: {content_config.example_identifier} ({version_tag})")
            
            # Recursively deploy nested contents
            if content_config.contents:
                # Create a temporary course config with just the nested contents
                nested_config = type('obj', (object,), {'contents': content_config.contents})()
                _deploy_course_contents(course_id, nested_config, auth, full_path, position_counter)
                
        except Exception as e:
            click.echo(f"    ❌ Failed to create content {content_config.title}: {e}")


def _generate_student_templates(config: ComputorDeploymentConfig, auth: CLIAuthConfig):
    """Generate GitLab student template repositories for courses with contents."""
    
    click.echo(f"\n🚀 Generating student template repositories...")
    
    # Get API clients
    org_client = get_crud_client(auth, OrganizationInterface)
    family_client = get_crud_client(auth, CourseFamilyInterface)
    course_client = get_crud_client(auth, CourseInterface)
    custom_client = get_custom_client(auth)
    
    generated_count = 0
    failed_count = 0
    
    # Process each organization
    for org_config in config.organizations:
        # Find the organization
        orgs = org_client.list(OrganizationQuery(path=org_config.path))
        if not orgs:
            continue
        org = orgs[0]
        
        # Process each course family
        for family_config in org_config.course_families:
            # Find the course family
            families = family_client.list(CourseFamilyQuery(
                organization_id=str(org.id),
                path=family_config.path
            ))
            if not families:
                continue
            family = families[0]
            
            # Process each course
            for course_config in family_config.courses:
                # Only process courses that have contents defined
                if not course_config.contents:
                    continue
                    
                # Find the course
                courses = course_client.list(CourseQuery(
                    course_family_id=str(family.id),
                    path=course_config.path
                ))
                if not courses:
                    continue
                course = courses[0]
                
                # Generate student template for this course
                try:
                    click.echo(f"  Generating template for: {course_config.name} ({course_config.path})")
                    result = custom_client.create(f"system/courses/{course.id}/generate-student-template", {})
                    
                    if result and result.get('workflow_id'):
                        click.echo(f"    ✅ Template generation started (workflow: {result.get('workflow_id')})")
                        generated_count += 1
                    else:
                        click.echo(f"    ⚠️  Template generation response unclear")
                        failed_count += 1
                except Exception as e:
                    click.echo(f"    ❌ Failed to generate template: {e}")
                    failed_count += 1
    
    # Summary
    if generated_count > 0 or failed_count > 0:
        click.echo(f"\n📊 Student Template Generation Summary:")
        click.echo(f"  ✅ Successfully initiated: {generated_count} templates")
        if failed_count > 0:
            click.echo(f"  ❌ Failed: {failed_count} templates")


def _link_backends_to_deployed_courses(config: ComputorDeploymentConfig, auth: CLIAuthConfig, generate_student_template: bool = False):
    """Link execution backends to all deployed courses and create course contents."""
    
    click.echo(f"\n🔗 Linking execution backends to courses...")
    
    # Get API clients
    org_client = get_crud_client(auth, OrganizationInterface)
    family_client = get_crud_client(auth, CourseFamilyInterface)
    course_client = get_crud_client(auth, CourseInterface)
    
    # Process each organization
    for org_config in config.organizations:
        # Find the organization
        orgs = org_client.list(OrganizationQuery(path=org_config.path))
        if not orgs:
            click.echo(f"  ⚠️  Organization not found: {org_config.path}")
            continue
        org = orgs[0]
        
        # Process each course family
        for family_config in org_config.course_families:
            # Find the course family
            families = family_client.list(CourseFamilyQuery(
                organization_id=str(org.id),
                path=family_config.path
            ))
            if not families:
                click.echo(f"  ⚠️  Course family not found: {family_config.path}")
                continue
            family = families[0]
            
            # Process each course
            for course_config in family_config.courses:
                # Find the course
                courses = course_client.list(CourseQuery(
                    course_family_id=str(family.id),
                    path=course_config.path
                ))
                if not courses:
                    click.echo(f"  ⚠️  Course not found: {course_config.path}")
                    continue
                course = courses[0]
                
                click.echo(f"  Course: {course_config.name} ({course_config.path})")
                
                # Link execution backends to this course
                if course_config.execution_backends:
                    _link_execution_backends_to_course(
                        str(course.id),
                        course_config.execution_backends,
                        auth
                    )
                
                # Deploy course contents
                if course_config.contents:
                    click.echo(f"\n📚 Creating course contents for {course_config.name}...")
                    _deploy_course_contents(str(course.id), course_config, auth)
    
    # Generate student templates if requested
    if generate_student_template:
        _generate_student_templates(config, auth)


def _link_execution_backends_to_course(course_id: str, execution_backends: list, auth: CLIAuthConfig):
    """Link execution backends to a course."""
    
    if not execution_backends:
        return
    
    # Get API clients
    backend_client = get_crud_client(auth, ExecutionBackendInterface)
    course_backend_client = get_crud_client(auth, CourseExecutionBackendInterface)
    
    for backend_ref in execution_backends:
        try:
            # Find the backend by slug
            backends = backend_client.list(ExecutionBackendQuery(slug=backend_ref.slug))
            
            if not backends:
                click.echo(f"      ⚠️  Backend not found: {backend_ref.slug}")
                continue
            
            backend = backends[0]
            
            # Check if link already exists
            existing_links = course_backend_client.list(CourseExecutionBackendQuery(
                course_id=course_id,
                execution_backend_id=str(backend.id)
            ))
            
            if existing_links:
                click.echo(f"      ℹ️  Backend already linked: {backend_ref.slug}")
                
                # Update properties if provided
                if backend_ref.properties:
                    link = existing_links[0]
                    link_update = {
                        'properties': backend_ref.properties
                    }
                    course_backend_client.update(str(link.id), link_update)
                    click.echo(f"      ✅ Updated link properties for: {backend_ref.slug}")
            else:
                # Create new link
                link_create = CourseExecutionBackendCreate(
                    course_id=course_id,
                    execution_backend_id=str(backend.id),
                    properties=backend_ref.properties or {}
                )
                course_backend_client.create(link_create)
                click.echo(f"      ✅ Linked backend: {backend_ref.slug}")
                
        except Exception as e:
            click.echo(f"      ❌ Failed to link backend {backend_ref.slug}: {e}")


def _ensure_example_repository(repo_name: str, auth: CLIAuthConfig):
    """Find or create an example repository with MinIO backend."""
    repo_client = get_crud_client(auth, ExampleRepositoryInterface)

    # Try find by name
    try:
        existing = repo_client.list(ExampleRepositoryQuery(name=repo_name))
        if existing:
            return existing[0]
    except Exception:
        pass

    # Create default MinIO-backed repository
    try:
        repo_create = ExampleRepositoryCreate(
            name=repo_name,
            description=f"Repository for {repo_name} examples",
            source_type="minio",
            source_url="examples-bucket/local",
        )
        return repo_client.create(repo_create)
    except Exception as e:
        raise RuntimeError(f"Failed to create example repository '{repo_name}': {e}")


def _create_zip_bytes_from_directory(directory_path: Path) -> bytes:
    """Create a zip archive from a directory; ensure meta.yaml exists.

    - Skips hidden files/dirs (starting with '.')
    - If meta.yaml is missing, generates a minimal one
    """
    # Determine if meta.yaml exists
    meta_path = directory_path / "meta.yaml"
    needs_meta = not meta_path.is_file()

    # Prepare in-memory zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        # Add all non-hidden files recursively
        for file_path in directory_path.rglob("*"):
            rel = file_path.relative_to(directory_path)
            # Skip hidden files/dirs
            parts = rel.parts
            if any(part.startswith(".") for part in parts):
                continue
            if file_path.is_file():
                zipf.write(file_path, arcname=str(rel))

        # Inject minimal meta.yaml if missing
        if needs_meta:
            minimal_meta = (
                "title: "
                + directory_path.name.replace('-', ' ').replace('_', ' ').title()
                + "\n"
                + f"description: Example from {directory_path.name}\n"
                + "language: en\n"
            )
            zipf.writestr("meta.yaml", minimal_meta)

    return zip_buffer.getvalue()


def _read_meta_and_dependencies(example_dir: Path) -> tuple[str, list[str]]:
    """Read meta.yaml from a directory and return (slug, dependencies).

    - Slug comes from meta.yaml 'slug' or falls back to directory name mapped to dots
    - Dependencies are read from either 'properties.testDependencies' or 'testDependencies'
      and normalized to a list of slugs
    """
    meta_path = example_dir / "meta.yaml"
    slug = example_dir.name.replace('-', '.').replace('_', '.')
    dependencies: list[str] = []

    if meta_path.is_file():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f) or {}
        except Exception:
            meta = {}
        slug = meta.get('slug', slug)

        # testDependencies can be in meta['properties']['testDependencies'] or meta['testDependencies']
        td = None
        if isinstance(meta.get('properties'), dict) and 'testDependencies' in meta['properties']:
            td = meta['properties'].get('testDependencies')
        elif 'testDependencies' in meta:
            td = meta.get('testDependencies')

        if isinstance(td, list):
            for item in td:
                if isinstance(item, str):
                    dependencies.append(item)
                elif isinstance(item, dict) and 'slug' in item:
                    dependencies.append(item['slug'])
    return slug, dependencies


def _toposort_by_dependencies(subdirs: list[Path]) -> list[Path]:
    """Topologically sort example directories so dependencies come first.

    - Builds a graph based on meta.yaml testDependencies slugs
    - Only considers dependencies that are present in the batch
    - On cycles, falls back to appending remaining nodes in stable order
    """
    # Build slug mapping and deps
    slug_to_dir: dict[str, Path] = {}
    deps_map: dict[str, set[str]] = {}

    for d in subdirs:
        slug, deps = _read_meta_and_dependencies(d)
        slug_to_dir[slug] = d
        deps_map[slug] = set(deps)

    # Reduce dependencies to only those within this batch
    for slug, deps in deps_map.items():
        deps_map[slug] = set(dep for dep in deps if dep in slug_to_dir)

    # Compute in-degrees
    in_degree: dict[str, int] = {slug: 0 for slug in slug_to_dir}
    for slug, deps in deps_map.items():
        for dep in deps:
            in_degree[slug] += 1

    # Kahn's algorithm
    queue = [slug for slug, deg in in_degree.items() if deg == 0]
    queue.sort()  # stable order
    ordered_slugs: list[str] = []

    # Build reverse edges: dep -> [slug]
    rev: dict[str, set[str]] = {s: set() for s in slug_to_dir}
    for slug, deps in deps_map.items():
        for dep in deps:
            rev[dep].add(slug)

    while queue:
        s = queue.pop(0)
        ordered_slugs.append(s)
        for nxt in sorted(rev.get(s, [])):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    # If there are nodes left (cycle), append them in deterministic order
    if len(ordered_slugs) < len(slug_to_dir):
        remaining = [s for s in slug_to_dir if s not in ordered_slugs]
        ordered_slugs.extend(sorted(remaining))

    return [slug_to_dir[s] for s in ordered_slugs]


def _upload_examples_from_directory(examples_dir: Path, repo_name: str, auth: CLIAuthConfig, custom_client: CustomClient):
    """Upload each subdirectory in examples_dir as a zipped example to the API.

    The upload order is topologically sorted by dependencies found in meta.yaml.
    """
    if not examples_dir.exists() or not examples_dir.is_dir():
        click.echo(f"⚠️  Examples directory not found or not a directory: {examples_dir}")
        return

    # Ensure repository exists
    repo = _ensure_example_repository(repo_name, auth)
    repo_id = str(repo.id)

    # Collect immediate subdirectories
    subdirs = [d for d in examples_dir.iterdir() if d.is_dir()]
    if not subdirs:
        click.echo(f"ℹ️  No example subdirectories found in {examples_dir}")
        return

    # Sort by dependencies so prerequisites upload first
    ordered_subdirs = _toposort_by_dependencies(subdirs)

    click.echo(f"\n📦 Uploading {len(ordered_subdirs)} example(s) from '{examples_dir}' to repository '{repo_name}'...")

    uploaded = 0
    failed = 0
    for subdir in ordered_subdirs:
        try:
            # Create zip bytes (ensure meta.yaml is included)
            zip_bytes = _create_zip_bytes_from_directory(subdir)
            b64_zip = base64.b64encode(zip_bytes).decode("ascii")

            payload = {
                "repository_id": repo_id,
                "directory": subdir.name,
                "files": {f"{subdir.name}.zip": b64_zip},
            }

            # Upload
            custom_client.create("examples/upload", payload)
            click.echo(f"  ✅ Uploaded example: {subdir.name}")
            uploaded += 1
        except Exception as e:
            click.echo(f"  ❌ Failed to upload {subdir.name}: {e}")
            failed += 1

    click.echo(f"📊 Example upload summary — success: {uploaded}, failed: {failed}, total: {len(subdirs)}")


@deployment.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate configuration without deploying'
)
@click.option(
    '--wait',
    is_flag=True,
    default=True,
    help='Wait for deployment to complete'
)
@click.option(
    '--generate-student-template',
    is_flag=True,
    default=False,
    help='Generate GitLab student template repositories after creating course contents'
)
@authenticate
def apply(config_file: str, dry_run: bool, wait: bool, generate_student_template: bool, auth: CLIAuthConfig):
    """
    Apply a deployment configuration to create the hierarchy.
    
    This command reads a YAML deployment configuration and creates the
    organization -> course family -> course structure using Temporal workflows.
    """
    click.echo(f"Loading deployment configuration from {config_file}...")
    
    # Load and parse the YAML file
    try:
        with open(config_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        # Validate by creating the config object
        config = ComputorDeploymentConfig(**yaml_data)
        click.echo("✅ Configuration validated successfully")
        
        if dry_run:
            click.echo("\n--- Deployment Plan (Dry Run) ---")
            
            # Show entity counts
            counts = config.count_entities()
            click.echo(f"Total: {counts['organizations']} organizations, {counts['course_families']} course families, {counts['courses']} courses")
            if counts.get('users', 0) > 0:
                click.echo(f"       {counts['users']} users, {counts['course_members']} course memberships")
            
            # Show execution backends to be created
            if config.execution_backends:
                click.echo(f"\nExecution Backends to create/update:")
                for backend in config.execution_backends:
                    click.echo(f"  - {backend.slug} (type: {backend.type})")
                    if backend.properties:
                        click.echo(f"    Properties: {backend.properties}")
            
            # Show hierarchical structure
            for org_idx, org in enumerate(config.organizations):
                click.echo(f"\nOrganization {org_idx + 1}: {org.name} ({org.path})")
                if org.gitlab:
                    click.echo(f"  GitLab: {org.gitlab.url} (parent: {org.gitlab.parent or 'root'})")
                
                for family_idx, family in enumerate(org.course_families):
                    click.echo(f"  Course Family {family_idx + 1}: {family.name} ({family.path})")
                    
                    for course_idx, course in enumerate(family.courses):
                        click.echo(f"    Course {course_idx + 1}: {course.name} ({course.path})")
                        if course.execution_backends:
                            backend_refs = [ref.slug for ref in course.execution_backends]
                            click.echo(f"      Backend references: {', '.join(backend_refs)}")
            
            # Show all paths that will be created
            paths = config.get_deployment_paths()
            if paths:
                click.echo(f"\nPaths to be created:")
                for path in paths:
                    click.echo(f"  - {path}")
            
            # Show users to be created
            if config.users:
                click.echo(f"\nUsers to be created:")
                for user_deployment in config.users:
                    user = user_deployment.user
                    click.echo(f"  - {user.display_name} ({user.username})")
                    if user_deployment.accounts:
                        for account in user_deployment.accounts:
                            click.echo(f"    Account: {account.type} @ {account.provider}")
                    if user_deployment.course_members:
                        for cm in user_deployment.course_members:
                            if cm.is_path_based:
                                member_str = f"    Member: {cm.organization}/{cm.course_family}/{cm.course} as {cm.role}"
                                if cm.group:
                                    member_str += f" (group: {cm.group})"
                                click.echo(member_str)
                            elif cm.is_id_based:
                                member_str = f"    Member: Course {cm.id} as {cm.role}"
                                if cm.group:
                                    member_str += f" (group: {cm.group})"
                                click.echo(member_str)
            
            click.echo("\n✅ Dry run completed. No changes made.")
            return
        
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # Setup client with authentication
    custom_client = get_custom_client(auth)
    
    # Deploy execution backends first (before hierarchy)
    if config.execution_backends:
        _deploy_execution_backends(config, auth)
    
    # Optionally upload examples prior to starting hierarchy deployment
    if getattr(config, 'examples_upload', None):
        cfg_dir = Path(config_file).parent
        rel_path = Path(config.examples_upload.path)
        resolved_path = rel_path if rel_path.is_absolute() else (cfg_dir / rel_path).resolve()
        click.echo(f"\n🔼 Preparing example uploads from: {resolved_path}")
        _upload_examples_from_directory(resolved_path, config.examples_upload.repository, auth, custom_client)

    # Deploy using API endpoint
    click.echo(f"\nStarting deployment via API...")
    
    payload = {
        "deployment_config": config.model_dump(),
        "validate_only": False
    }
    
    try:
        # Send deployment request
        result = custom_client.create("system/hierarchy/create", payload)
        
        if result:
            click.echo(f"✅ Deployment workflow started!")
            click.echo(f"  Workflow ID: {result.get('workflow_id')}")
            click.echo(f"  Status: {result.get('status')}")
            click.echo(f"  Path: {result.get('deployment_path')}")
            
            if wait and result.get('workflow_id'):
                # Poll for status
                click.echo("\nWaiting for deployment to complete...")
                import time
                workflow_id = result.get('workflow_id')
                
                for _ in range(60):  # Wait up to 5 minutes
                    time.sleep(5)
                    try:
                        status_data = custom_client.get(f"system/hierarchy/status/{workflow_id}")
                        if status_data.get('status') == 'completed':
                            click.echo("\n✅ Deployment completed successfully!")
                            
                            # Link execution backends to courses and create contents
                            _link_backends_to_deployed_courses(config, auth, generate_student_template)
                            
                            # Deploy users if configured
                            if config.users:
                                click.echo(f"\n📥 Creating {len(config.users)} users...")
                                _deploy_users(config, auth)
                            break
                        elif status_data.get('status') == 'failed':
                            click.echo(f"\n❌ Deployment failed: {status_data.get('error')}", err=True)
                            sys.exit(1)
                        click.echo(".", nl=False)
                    except Exception as e:
                        click.echo(f"\n⚠️  Error checking status: {e}")
                        break
                else:
                    click.echo("\n⚠️  Deployment is still running. Check status later.")
            
            # If not waiting but deployment started, try to continue with remaining tasks
            if not wait:
                click.echo(f"\n⚠️  Continuing without waiting for hierarchy deployment...")
                # Try to link backends and create contents (might fail if hierarchy not ready)
                _link_backends_to_deployed_courses(config, auth, generate_student_template)
                
                if config.users:
                    click.echo(f"\n📥 Creating {len(config.users)} users (hierarchy might still be deploying)...")
                    _deploy_users(config, auth)
        else:
            click.echo("❌ Failed to start deployment", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error during deployment: {e}", err=True)
        sys.exit(1)


@deployment.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file: str):
    """
    Validate a deployment configuration file.
    
    This checks that the YAML is valid and all required fields are present.
    """
    click.echo(f"Validating {config_file}...")
    
    try:
        with open(config_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        # Validate by creating the config object
        config = ComputorDeploymentConfig(**yaml_data)
        
        click.echo("✅ Configuration is valid!")
        
        # Show entity counts
        counts = config.count_entities()
        click.echo(f"\nSummary:")
        click.echo(f"  Organizations: {counts['organizations']}")
        click.echo(f"  Course Families: {counts['course_families']}")
        click.echo(f"  Courses: {counts['courses']}")
        if counts.get('users', 0) > 0:
            click.echo(f"  Users: {counts['users']}")
            click.echo(f"  Course Memberships: {counts['course_members']}")
        
        # Show paths
        paths = config.get_deployment_paths()
        if paths:
            click.echo(f"\nPaths:")
            for path in paths:
                click.echo(f"  - {path}")
        
        # Check for potential issues
        warnings = []
        gitlab_configured = any(org.gitlab for org in config.organizations)
        execution_backends_configured = any(
            course.execution_backends 
            for org in config.organizations 
            for family in org.course_families 
            for course in family.courses
        )
        
        if not gitlab_configured:
            warnings.append("No GitLab configuration specified for any organization")
        if not execution_backends_configured:
            warnings.append("No execution backends configured for any course")
        
        if warnings:
            click.echo(f"\n⚠️  Warnings:")
            for warning in warnings:
                click.echo(f"  - {warning}")
        
    except yaml.YAMLError as e:
        click.echo(f"❌ Invalid YAML format: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Invalid configuration: {e}", err=True)
        sys.exit(1)


@deployment.command()
def list_examples():
    """List available example deployment formats."""
    click.echo("Available deployment configuration examples:\n")
    
    examples = {
        "minimal": "Single organization with one course family and one course",
        "tutorial": "Simple single organization deployment (default)",
        "full": "Multi-organization deployment with multiple course families and courses"
    }
    
    for name, description in examples.items():
        click.echo(f"  {name:10} - {description}")
    
    click.echo("\nGenerate an example with: ctutor deployment init --format <name>")


# Main command group
@click.group()
def deploy():
    """Deployment management commands."""
    pass


deploy.add_command(deployment, "deployment")
