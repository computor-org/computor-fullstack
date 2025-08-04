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


class CourseContentTypeConfig(BaseDeployment):
    """Course content type configuration for deployment."""
    slug: str = Field(description="Unique identifier for the content type")
    title: Optional[str] = Field(None, description="Display title for the content type")
    description: Optional[str] = Field(None, description="Description of the content type")
    color: Optional[str] = Field("green", description="Display color (hex, rgb, hsl, or named color)")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional properties")
    course_content_kind_id: str = Field(description="ID of the course content kind (e.g., 'assignment', 'unit')")


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
    projects: Optional[CourseProjects] = Field(None, description="Course project structure")
    execution_backends: Optional[List[ExecutionBackendConfig]] = Field(
        default_factory=list, 
        description="Available execution backends for this course"
    )
    content_types: Optional[List[CourseContentTypeConfig]] = Field(
        default_factory=list,
        description="Course content types to be created (assignments, units, etc.)"
    )
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Course-specific settings")


# Hierarchical configuration classes for nested structure

class HierarchicalCourseConfig(CourseConfig):
    """Course configuration for hierarchical deployment."""
    pass  # Inherits all fields from CourseConfig


class HierarchicalCourseFamilyConfig(CourseFamilyConfig):
    """Course family configuration with nested courses."""
    courses: List[HierarchicalCourseConfig] = Field(
        default_factory=list,
        description="List of courses in this course family"
    )


class HierarchicalOrganizationConfig(OrganizationConfig):
    """Organization configuration with nested course families."""
    course_families: List[HierarchicalCourseFamilyConfig] = Field(
        default_factory=list,
        description="List of course families in this organization"
    )


class ComputorDeploymentConfig(BaseDeployment):
    """
    Hierarchical deployment configuration for creating organization -> course family -> course structures.
    
    Supports deploying multiple organizations, each with multiple course families and courses.
    """
    # Hierarchical structure - list of organizations with nested course families and courses
    organizations: List[HierarchicalOrganizationConfig] = Field(
        description="List of organizations with nested course families and courses"
    )
    
    # Global deployment settings
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Global deployment settings"
    )
    
    def validate_structure(self) -> bool:
        """Validate the deployment configuration structure."""
        return len(self.organizations) > 0
    
    def count_entities(self) -> Dict[str, int]:
        """Count the total number of entities to be created."""
        org_count = len(self.organizations)
        family_count = sum(len(org.course_families) for org in self.organizations)
        course_count = sum(
            len(family.courses) 
            for org in self.organizations 
            for family in org.course_families
        )
        return {
            "organizations": org_count, 
            "course_families": family_count, 
            "courses": course_count
        }
    
    def get_deployment_paths(self) -> List[str]:
        """Get all the hierarchical paths that will be created."""
        paths = []
        for org in self.organizations:
            for family in org.course_families:
                for course in family.courses:
                    paths.append(f"{org.path}/{family.path}/{course.path}")
        return paths
    
    def get_full_course_path(self) -> str:
        """Get the full course path for the primary deployment."""
        if not self.organizations:
            return ""
        
        # Return the first organization/course family/course path
        org = self.organizations[0]
        if not org.course_families:
            return org.path
        
        family = org.course_families[0]
        if not family.courses:
            return f"{org.path}/{family.path}"
        
        course = family.courses[0]
        return f"{org.path}/{family.path}/{course.path}"


# Example deployment configurations

# Simple single organization deployment
EXAMPLE_DEPLOYMENT = ComputorDeploymentConfig(
    organizations=[
        HierarchicalOrganizationConfig(
            name="Computer Science Department",
            path="cs-dept",
            description="Department of Computer Science",
            gitlab=GitLabConfig(
                url="https://gitlab.example.com",
                token="<token>",
                parent=0
            ),
            course_families=[
                HierarchicalCourseFamilyConfig(
                    name="Programming Fundamentals",
                    path="programming",
                    description="Core programming courses",
                    courses=[
                        HierarchicalCourseConfig(
                            name="Python Programming",
                            path="python-2025s",
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
                            content_types=[
                                CourseContentTypeConfig(
                                    slug="homework",
                                    title="Homework Assignment",
                                    description="Weekly homework assignments",
                                    color="blue",
                                    course_content_kind_id="assignment"
                                ),
                                CourseContentTypeConfig(
                                    slug="exam",
                                    title="Exam",
                                    description="Course examinations",
                                    color="red",
                                    course_content_kind_id="assignment"
                                ),
                                CourseContentTypeConfig(
                                    slug="lecture",
                                    title="Lecture Material",
                                    description="Lecture notes and materials",
                                    color="green",
                                    course_content_kind_id="unit"
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# Multi-organization deployment example
EXAMPLE_MULTI_DEPLOYMENT = ComputorDeploymentConfig(
    organizations=[
        HierarchicalOrganizationConfig(
            name="Technical University",
            path="tech-uni",
            description="Technical University Computer Science",
            gitlab=GitLabConfig(
                url="https://gitlab.example.com",
                token="<token>",
                parent=0
            ),
            course_families=[
                HierarchicalCourseFamilyConfig(
                    name="Programming Fundamentals",
                    path="programming",
                    description="Core programming courses",
                    courses=[
                        HierarchicalCourseConfig(
                            name="Python Programming",
                            path="python-2025s",
                            description="Introduction to Python programming",
                            execution_backends=[
                                ExecutionBackendConfig(
                                    slug="python-3.11",
                                    type="python",
                                    version="3.11",
                                    settings={"timeout": 30}
                                )
                            ]
                        ),
                        HierarchicalCourseConfig(
                            name="Java Programming",
                            path="java-2025s",
                            description="Introduction to Java programming",
                            execution_backends=[
                                ExecutionBackendConfig(
                                    slug="java-17",
                                    type="java",
                                    version="17",
                                    settings={"timeout": 45}
                                )
                            ]
                        )
                    ]
                ),
                HierarchicalCourseFamilyConfig(
                    name="Data Science",
                    path="data-science",
                    description="Data analysis and machine learning",
                    courses=[
                        HierarchicalCourseConfig(
                            name="Statistics with R",
                            path="stats-r-2025s",
                            description="Statistical analysis using R",
                            execution_backends=[
                                ExecutionBackendConfig(
                                    slug="r-4.3",
                                    type="r",
                                    version="4.3",
                                    settings={"timeout": 60}
                                )
                            ]
                        )
                    ]
                )
            ]
        ),
        HierarchicalOrganizationConfig(
            name="Business School",
            path="business",
            description="Business School IT Department",
            course_families=[
                HierarchicalCourseFamilyConfig(
                    name="Business Analytics",
                    path="analytics",
                    description="Data analysis for business",
                    courses=[
                        HierarchicalCourseConfig(
                            name="Excel Analytics",
                            path="excel-2025s",
                            description="Advanced Excel for business analysis"
                        )
                    ]
                )
            ]
        )
    ],
    settings={
        "deployment_notes": "Multi-university deployment example",
        "created_by": "system_admin"
    }
)