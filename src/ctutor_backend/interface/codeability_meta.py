"""
CodeAbility Meta Models for Assignment Repository Structure

This module defines the Pydantic models for meta.yaml files at different levels 
of the assignments repository hierarchy:

1. Root Level (Course): CodeAbilityCourseMeta - defines the overall course
2. Unit Level: CodeAbilityUnitMeta - defines units or content kinds with ascends
3. Assignment Level: CodeAbilityExampleMeta - defines individual assignments/examples

Each level has its own meta.yaml file with specific fields appropriate for that level.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_yaml import to_yaml_str


class LanguageEnum(str, Enum):
    """Supported languages for course content."""
    de = "de"
    en = "en"


class MetaTypeEnum(str, Enum):
    """Types of meta.yaml files in the hierarchy."""
    Course = "course"
    Unit = "unit"
    Assignment = "assignment"


class QualificationEnum(str, Enum):
    """Test qualification types."""
    verifyEqual = "verifyEqual"
    matches = "matches"
    contains = "contains"
    startsWith = "startsWith"
    endsWith = "endsWith"
    count = "count"
    regexp = "regexp"


class TypeEnum(str, Enum):
    """Test types for assignments."""
    variable = "variable"
    graphics = "graphics"
    structural = "structural"
    linting = "linting"
    exist = "exist"
    error = "error"
    warning = "warning"
    help = "help"
    stdout = "stdout"


class StatusEnum(str, Enum):
    """Execution status for assignments."""
    scheduled = "SCHEDULED"
    completed = "COMPLETED"
    timedout = "TIMEDOUT"
    crashed = "CRASHED"
    cancelled = "CANCELLED"
    skipped = "SKIPPED"
    failed = "FAILED"


class ResultEnum(str, Enum):
    """Test result types."""
    passed = "PASSED"
    failed = "FAILED"
    skipped = "SKIPPED"


# Version regex pattern
VERSION_REGEX = "^([1-9]\\d*|0)(\\.(([1-9]\\d*)|0)){0,3}$"


class CodeAbilityBase(BaseModel):
    """Base class for all CodeAbility meta models."""
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        coerce_numbers_to_str=True
    )

    def get_yaml(self) -> str:
        """Generate YAML representation of the model."""
        return to_yaml_str(self, exclude_none=True)

    def write_yaml(self, filename: str) -> None:
        """Write the model to a YAML file."""
        with open(filename, "w") as file:
            file.write(self.get_yaml())


class CodeAbilityLink(CodeAbilityBase):
    """Link to external resources."""
    description: str = Field(min_length=0, description="Description of the link")
    url: str = Field(min_length=1, description="URL of the link")


class CodeAbilityPerson(CodeAbilityBase):
    """Person information for authors/maintainers."""
    name: Optional[str] = Field(None, min_length=1, description="Full name")
    email: Optional[str] = Field(None, min_length=1, description="Email address")
    affiliation: Optional[str] = Field(None, min_length=1, description="Institutional affiliation")


class CourseExecutionBackendConfig(CodeAbilityBase):
    """Configuration for course execution backend."""
    slug: str = Field(description="Unique identifier for the execution backend")
    settings: Optional[dict] = Field(None, description="Backend-specific settings")


class TypeConfig(CodeAbilityBase):
    """Configuration for content types."""
    kind: str = Field(description="Type of content (e.g., 'assignment', 'unit')")
    slug: str = Field(description="Unique identifier for the content type")
    title: str = Field(description="Human-readable title")
    color: Optional[str] = Field(None, description="Color for UI representation")
    description: Optional[str] = Field(None, description="Description of the content type")
    properties: dict = Field(default_factory=dict, description="Additional properties")


class CodeAbilityMetaProperties(CodeAbilityBase):
    """Properties specific to assignment-level meta."""
    studentSubmissionFiles: Optional[List[str]] = Field(
        default_factory=list,
        description="Files that students must submit"
    )
    additionalFiles: Optional[List[str]] = Field(
        default_factory=list,
        description="Additional files provided to students"
    )
    testFiles: Optional[List[str]] = Field(
        default_factory=list,
        description="Test files for automated grading"
    )
    studentTemplates: Optional[List[str]] = Field(
        default_factory=list,
        description="Template files for student projects"
    )
    executionBackend: Optional[CourseExecutionBackendConfig] = Field(
        None,
        description="Execution backend configuration for this assignment"
    )
    maxTestRuns: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of test runs allowed"
    )
    maxSubmissions: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of submissions allowed"
    )
    maxGroupSize: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum group size for collaborative assignments"
    )

    @field_validator('maxTestRuns', 'maxSubmissions', 'maxGroupSize', 'executionBackend', mode='before')
    @classmethod
    def empty_list_to_none(cls, value):
        """Convert empty lists to None."""
        if isinstance(value, list) and len(value) == 0:
            return None
        return value


class CodeAbilityBaseMeta(CodeAbilityBase):
    """Base meta information common to all levels."""
    version: Optional[str] = Field(
        "1.0",
        pattern=VERSION_REGEX,
        description="Version of the meta format"
    )
    kind: Optional[MetaTypeEnum] = Field(
        MetaTypeEnum.Assignment,
        description="Type of content (course, unit, assignment)"
    )
    title: Optional[str] = Field(
        None,
        min_length=1,
        description="Human-readable title"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the content"
    )
    language: Optional[LanguageEnum] = Field(
        LanguageEnum.en,
        description="Primary language of the content"
    )
    license: Optional[str] = Field(
        "Not specified",
        min_length=1,
        description="License information"
    )
    authors: Optional[List[CodeAbilityPerson]] = Field(
        default_factory=list,
        description="Content authors"
    )
    maintainers: Optional[List[CodeAbilityPerson]] = Field(
        default_factory=list,
        description="Content maintainers"
    )
    links: Optional[List[CodeAbilityLink]] = Field(
        default_factory=list,
        description="Related links"
    )
    supportingMaterial: Optional[List[CodeAbilityLink]] = Field(
        default_factory=list,
        description="Supporting material links"
    )
    keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Keywords for categorization"
    )

    @field_validator('description', mode='before')
    @classmethod
    def empty_list_to_none(cls, value):
        """Convert empty lists to None for description."""
        if isinstance(value, list) and len(value) == 0:
            return None
        return value


class CodeAbilityExampleMeta(CodeAbilityBaseMeta):
    """
    Meta information for assignment/release level directories.
    
    This is used for individual assignments, examples, or exercises.
    Contains the most detailed information including submission requirements,
    test configuration, and execution settings.
    """
    kind: Optional[MetaTypeEnum] = Field(
        MetaTypeEnum.Assignment,
        description="Must be 'assignment' for release-level meta"
    )
    properties: Optional[CodeAbilityMetaProperties] = Field(
        default_factory=CodeAbilityMetaProperties,
        description="Assignment-specific properties"
    )


class CodeAbilityUnitMeta(CodeAbilityBaseMeta):
    """
    Meta information for unit/content kind directories.
    
    This is used for organizational units like chapters, modules, or thematic groups.
    Contains information about the unit structure and content organization.
    """
    kind: Optional[MetaTypeEnum] = Field(
        MetaTypeEnum.Unit,
        description="Must be 'unit' for unit-level meta"
    )
    type: str = Field(
        description="Content type slug (e.g., 'chapter', 'module', 'week')"
    )


class CodeAbilityCourseMeta(CodeAbilityBaseMeta):
    """
    Meta information for course root level.
    
    This is used at the root of the assignments repository to define
    the overall course structure, content types, and execution backends.
    """
    kind: Optional[MetaTypeEnum] = Field(
        MetaTypeEnum.Course,
        description="Must be 'course' for course-level meta"
    )
    contentTypes: Optional[List[TypeConfig]] = Field(
        default_factory=list,
        description="Available content types for this course"
    )
    executionBackends: Optional[List[CourseExecutionBackendConfig]] = Field(
        default_factory=list,
        description="Available execution backends for this course"
    )


# Legacy compatibility - keep the old CodeAbilityMeta for backward compatibility
class CodeAbilityMeta(CodeAbilityExampleMeta):
    """
    Legacy meta model for backward compatibility.
    
    This extends CodeAbilityExampleMeta with additional fields that were
    used in the original implementation.
    """
    type: str = Field(description="Content type (legacy field)")
    testDependencies: Optional[List[str]] = Field(
        default_factory=list,
        description="Test dependencies (legacy field)"
    )