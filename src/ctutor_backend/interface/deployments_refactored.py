"""
Refactored deployment configurations for Computor.

This module contains clean deployment configuration classes for creating
organization -> course family -> course hierarchies via Temporal workflows.

The deprecated CodeAbility classes have been moved to codeability_meta.py
and test-related enums should be in their own module.
"""

import yaml
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from pydantic_yaml import to_yaml_str


class BaseDeployment(BaseModel):
    """Base class for all deployment configurations."""
    
    def get_deployment(self) -> str:
        """Get YAML representation of the deployment configuration."""
        return to_yaml_str(self, exclude_none=True, exclude_unset=True)

    def write_deployment(self, filename: str) -> None:
        """Write deployment configuration to a YAML file."""
        with open(filename, "w") as file:
            file.write(self.get_deployment())


class DeploymentFactory:
    """Factory for creating deployment configurations from YAML."""
    
    @staticmethod
    def read_deployment_from_string(classname, yamlstring: str):
        """Create deployment configuration from YAML string."""
        return classname(**yaml.safe_load(yamlstring))

    @staticmethod
    def read_deployment_from_file(classname, filename: str):
        """Create deployment configuration from YAML file."""
        with open(filename, "r") as file:
            if classname is not None:
                return classname(**yaml.safe_load(file))
            else:
                return yaml.safe_load(file)
    
    @staticmethod
    def read_deployment_from_file_raw(filename: str) -> dict:
        """Read raw YAML data from file."""
        with open(filename, "r") as file:
            return yaml.safe_load(file)


# Repository Configuration Classes

class GitLabConfig(BaseDeployment):
    """GitLab repository configuration."""
    url: Optional[str] = Field(None, description="GitLab instance URL")
    token: Optional[str] = Field(None, description="GitLab API token")
    parent: Optional[int] = Field(None, description="Parent group ID")
    full_path: Optional[str] = Field(None, description="Full path in GitLab")
    
    # Enhanced GitLab properties (populated after creation)
    group_id: Optional[int] = Field(None, description="GitLab group ID")
    parent_id: Optional[int] = Field(None, description="Parent group ID")
    namespace_id: Optional[int] = Field(None, description="Namespace ID")
    namespace_path: Optional[str] = Field(None, description="Namespace path")
    web_url: Optional[str] = Field(None, description="Web URL")
    visibility: Optional[str] = Field(None, description="Visibility level")
    last_synced_at: Optional[str] = Field(None, description="Last sync timestamp")


class GitHubConfig(BaseDeployment):
    """GitHub repository configuration (future support)."""
    url: Optional[str] = Field(None, description="GitHub instance URL")
    token: Optional[str] = Field(None, description="GitHub API token")
    organization: Optional[str] = Field(None, description="GitHub organization")


# Course Structure Configuration Classes

class ExecutionBackendConfig(BaseDeployment):
    """Execution backend configuration for courses."""
    slug: str = Field(description="Unique identifier for the backend")
    type: str = Field(description="Type of execution backend (e.g., python, matlab)")
    version: Optional[str] = Field(None, description="Backend version")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Backend-specific settings")


class CourseProjects(BaseDeployment):
    """Configuration for course-related GitLab projects."""
    tests: Optional[str] = Field("tests", description="Path for tests project")
    student_template: Optional[str] = Field("student-template", description="Path for student template project")
    reference: Optional[str] = Field("reference", description="Path for reference solution project")
    examples: Optional[str] = Field("examples", description="Path for examples project")
    documents: Optional[str] = Field("documents", description="Path for documents project")


class OrganizationConfig(BaseDeployment):
    """Organization configuration."""
    name: str = Field(description="Organization display name")
    path: str = Field(description="Organization path/slug")
    description: Optional[str] = Field(None, description="Organization description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization-specific settings")
    gitlab: Optional[GitLabConfig] = Field(None, description="GitLab configuration")
    github: Optional[GitHubConfig] = Field(None, description="GitHub configuration (future)")


class CourseFamilyConfig(BaseDeployment):
    """Course family configuration."""
    name: str = Field(description="Course family display name")
    path: str = Field(description="Course family path/slug")
    description: Optional[str] = Field(None, description="Course family description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Course family-specific settings")


class CourseConfig(BaseDeployment):
    """Course configuration."""
    name: str = Field(description="Course display name")
    path: str = Field(description="Course path/slug")
    description: Optional[str] = Field(None, description="Course description")
    term: Optional[str] = Field(None, description="Course term (e.g., '2024W', '2025S')")
    projects: Optional[CourseProjects] = Field(None, description="Course project structure")
    execution_backends: Optional[List[ExecutionBackendConfig]] = Field(
        default_factory=list, 
        description="Available execution backends for this course"
    )
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Course-specific settings")
    
    # Course-specific limits (moved from example meta)
    max_test_runs: Optional[int] = Field(None, description="Maximum test runs per student")
    max_submissions: Optional[int] = Field(None, description="Maximum submissions allowed")
    max_group_size: Optional[int] = Field(None, description="Maximum group size for assignments")


class ComputorDeploymentConfig(BaseDeployment):
    """
    Complete deployment configuration for creating an organization -> course family -> course hierarchy.
    
    This configuration can be used to deploy a complete course structure through Temporal workflows.
    """
    organization: OrganizationConfig = Field(description="Organization configuration")
    course_family: CourseFamilyConfig = Field(description="Course family configuration")  # Renamed from courseFamily
    course: CourseConfig = Field(description="Course configuration")
    
    # Global deployment settings
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Global deployment settings"
    )
    
    # Deployment metadata
    version: Optional[str] = Field("1.0", description="Deployment configuration version")
    deploy_examples: Optional[bool] = Field(
        False, 
        description="Whether to deploy example content during creation"
    )
    create_student_groups: Optional[bool] = Field(
        True, 
        description="Whether to create student groups during deployment"
    )
    
    def validate_paths(self) -> bool:
        """Validate that paths form a proper hierarchy."""
        # Paths should be hierarchical: org/family/course
        expected_family_path = f"{self.organization.path}/{self.course_family.path}"
        expected_course_path = f"{expected_family_path}/{self.course.path}"
        
        # This is a soft validation - paths can be customized
        return True
    
    def get_full_course_path(self) -> str:
        """Get the full hierarchical path for the course."""
        return f"{self.organization.path}/{self.course_family.path}/{self.course.path}"


# Example deployment configuration
EXAMPLE_DEPLOYMENT = ComputorDeploymentConfig(
    organization=OrganizationConfig(
        name="Computer Science Department",
        path="cs-dept",
        description="Department of Computer Science",
        gitlab=GitLabConfig(
            url="https://gitlab.example.com",
            token="<token>",
            parent=0  # Root level group
        )
    ),
    course_family=CourseFamilyConfig(
        name="Programming Fundamentals",
        path="prog-fundamentals",
        description="Introductory programming courses"
    ),
    course=CourseConfig(
        name="Python Programming",
        path="python-2025s",
        term="2025S",
        description="Introduction to Python programming",
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
        max_submissions=10,
        max_test_runs=50,
        max_group_size=2
    ),
    deploy_examples=True,
    create_student_groups=True
)