"""
CLI commands for deployment operations.

This module provides commands for working with ComputorDeploymentConfig,
including generating example configurations and deploying hierarchies.
"""

import sys
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
    CourseProjects,
    EXAMPLE_DEPLOYMENT,
    EXAMPLE_MULTI_DEPLOYMENT
)
from .auth import authenticate
from .config import CLIAuthConfig
from ..client.crud_client import CustomClient


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
@authenticate
def apply(config_file: str, dry_run: bool, wait: bool, auth: CLIAuthConfig):
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
                            click.echo(f"      Backends: {', '.join(b.type + '-' + b.version for b in course.execution_backends)}")
            
            # Show all paths that will be created
            paths = config.get_deployment_paths()
            if paths:
                click.echo(f"\nPaths to be created:")
                for path in paths:
                    click.echo(f"  - {path}")
            
            click.echo("\n✅ Dry run completed. No changes made.")
            return
        
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # Setup client with authentication
    if auth.basic != None:
        custom_client = CustomClient(url_base=auth.api_url, auth=(auth.basic.username, auth.basic.password))
    elif auth.gitlab != None:
        custom_client = CustomClient(url_base=auth.api_url, glp_auth_header=auth.gitlab.model_dump())
    else:
        click.echo("❌ No valid authentication method found", err=True)
        sys.exit(1)
    
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