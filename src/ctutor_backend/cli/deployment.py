"""
CLI commands for deployment operations.

This module provides commands for working with ComputorDeploymentConfig,
including generating example configurations and deploying hierarchies.
"""

import os
import sys
import yaml
import click
from pathlib import Path
from typing import Optional

from ..interface.deployments_refactored import (
    ComputorDeploymentConfig,
    OrganizationConfig,
    CourseFamilyConfig,
    CourseConfig,
    GitLabConfig,
    ExecutionBackendConfig,
    CourseProjects,
    EXAMPLE_DEPLOYMENT
)
# Temporal client will be imported dynamically to avoid circular imports
from ..database import get_db
from ..model.auth import User


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
            organization=OrganizationConfig(
                name="My Organization",
                path="my-org"
            ),
            course_family=CourseFamilyConfig(
                name="My Courses",
                path="my-courses"
            ),
            course=CourseConfig(
                name="My First Course",
                path="course-2025"
            )
        )
    elif format == 'full':
        # Full configuration with all optional fields
        config = ComputorDeploymentConfig(
            organization=OrganizationConfig(
                name="Computer Science Department",
                path="cs-dept",
                description="Department of Computer Science",
                gitlab=GitLabConfig(
                    url="${GITLAB_URL:-http://localhost:8084}",
                    token="${GITLAB_TOKEN}",
                    parent=0
                ),
                settings={
                    "department": "Computer Science",
                    "university": "Technical University"
                }
            ),
            course_family=CourseFamilyConfig(
                name="Programming Courses",
                path="programming",
                description="Core programming courses",
                settings={
                    "level": "undergraduate",
                    "credits": 6
                }
            ),
            course=CourseConfig(
                name="Introduction to Python",
                path="python-2025s",
                description="Learn Python from basics to advanced",
                term="2025S",
                projects=CourseProjects(
                    tests="tests",
                    student_template="student-template",
                    reference="reference",
                    examples="examples",
                    documents="docs"
                ),
                execution_backends=[
                    ExecutionBackendConfig(
                        slug="python-3.11",
                        type="python",
                        version="3.11",
                        settings={"timeout": 30}
                    )
                ],
                settings={
                    "instructor": "Dr. Smith",
                    "start_date": "2025-03-01",
                    "end_date": "2025-06-30"
                }
            ),
            settings={
                "deployment_notes": "Production deployment"
            }
        )
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


@deployment.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate configuration without deploying'
)
@click.option(
    '--user-id',
    help='User ID for deployment (defaults to admin user)'
)
@click.option(
    '--wait',
    is_flag=True,
    default=True,
    help='Wait for deployment to complete'
)
def apply(config_file: str, dry_run: bool, user_id: Optional[str], wait: bool):
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
            click.echo(f"Organization: {config.organization.name} ({config.organization.path})")
            click.echo(f"Course Family: {config.course_family.name} ({config.course_family.path})")
            click.echo(f"Course: {config.course.name} ({config.course.path})")
            
            if config.organization.gitlab:
                click.echo(f"\nGitLab Integration:")
                click.echo(f"  URL: {config.organization.gitlab.url}")
                click.echo(f"  Parent: {config.organization.gitlab.parent or 'root'}")
            
            if config.course.execution_backends:
                click.echo(f"\nExecution Backends:")
                for backend in config.course.execution_backends:
                    click.echo(f"  - {backend.type} ({backend.slug})")
            
            click.echo("\n✅ Dry run completed. No changes made.")
            return
        
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # Get user ID
    if not user_id:
        # Try to get admin user from database
        db = next(get_db())
        try:
            admin_user = db.query(User).filter(User.username == "admin").first()
            if admin_user:
                user_id = str(admin_user.id)
            else:
                click.echo("❌ No admin user found. Please specify --user-id", err=True)
                sys.exit(1)
        finally:
            db.close()
    
    # Deploy using API endpoint
    click.echo(f"\nStarting deployment via API...")
    
    # Use the deployment API endpoint
    import requests
    import json
    
    # Get API URL from environment or use default
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    
    # Prepare the request
    endpoint = f"{api_url}/api/deploy/from-config"
    headers = {"Content-Type": "application/json"}
    
    # Check for auth token
    auth_token = os.environ.get("API_TOKEN")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    payload = {
        "deployment_config": config.model_dump(),
        "validate_only": False
    }
    
    try:
        # Send deployment request
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
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
                    status_response = requests.get(
                        f"{api_url}/api/deploy/status/{workflow_id}",
                        headers=headers
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            click.echo("✅ Deployment completed successfully!")
                            break
                        elif status_data.get('status') == 'failed':
                            click.echo(f"❌ Deployment failed: {status_data.get('error')}", err=True)
                            sys.exit(1)
                    click.echo(".", nl=False)
                else:
                    click.echo("\n⚠️  Deployment is still running. Check status later.")
                    
        elif response.status_code == 401:
            click.echo("❌ Authentication required. Set API_TOKEN environment variable.", err=True)
            sys.exit(1)
        elif response.status_code == 403:
            click.echo("❌ Admin permissions required for deployment.", err=True)
            sys.exit(1)
        else:
            click.echo(f"❌ Deployment failed: {response.text}", err=True)
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        click.echo(f"❌ Cannot connect to API at {api_url}. Is the server running?", err=True)
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
        click.echo(f"\nSummary:")
        click.echo(f"  Organization: {config.organization.name}")
        click.echo(f"  Course Family: {config.course_family.name}")
        click.echo(f"  Course: {config.course.name}")
        click.echo(f"  Full Path: {config.get_full_course_path()}")
        
        # Check for potential issues
        warnings = []
        if not config.organization.gitlab:
            warnings.append("No GitLab configuration specified")
        if not config.course.execution_backends:
            warnings.append("No execution backends configured")
        
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
        "minimal": "Bare minimum configuration with only required fields",
        "tutorial": "Tutorial configuration with common settings (default)",
        "full": "Complete configuration showing all available options"
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