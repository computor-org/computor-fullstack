"""
CodeAbility Meta Models for Assignment/Example Metadata

This module defines the Pydantic models for meta.yaml files in example directories.
Each example contains a single meta.yaml file describing the assignment properties,
files, execution backend, and other metadata.

Examples are course-agnostic and can be assigned to multiple courses through
the CourseContent model which links examples to specific course contexts.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_yaml import to_yaml_str


# Language is now a string type to support any language
# class LanguageEnum(str, Enum):
#     """Supported languages for course content."""
#     de = "de"
#     en = "en"


# MetaTypeEnum removed - kind field is obsolete since we only handle assignments


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
    version: str = Field(description="Version of the execution backend (e.g., 'r2024b', 'v1.0')")
    settings: Optional[dict] = Field(None, description="Backend-specific settings")


# TypeConfig removed - content types are managed at CourseContent level, not in examples


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
    testDependencies: Optional[List[str]] = Field(
        default_factory=list,
        description="List of example identifiers that this example depends on (e.g., functions called from other examples)"
    )
    executionBackend: Optional[CourseExecutionBackendConfig] = Field(
        None,
        description="Execution backend configuration for this assignment"
    )
    # Course-dependent fields removed - these belong to course configuration, not example metadata
    # maxTestRuns, maxSubmissions, maxGroupSize are course/term specific and should be
    # configured at the CourseContent or Course level, not in the example meta.yaml

    @field_validator('executionBackend', mode='before')
    @classmethod
    def empty_list_to_none(cls, value):
        """Convert empty lists to None."""
        if isinstance(value, list) and len(value) == 0:
            return None
        return value


class CodeAbilityMeta(CodeAbilityBase):
    """Meta information for assignments/examples."""
    version: Optional[str] = Field(
        "1.0",
        pattern=VERSION_REGEX,
        description="Version of the meta format"
    )
    slug: Optional[str] = Field(
        None,
        description="Unique identifier for the assignment"
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
    language: Optional[str] = Field(
        "en",
        description="Primary language of the content (e.g., 'en', 'de', 'fr', etc.)"
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
    properties: Optional[CodeAbilityMetaProperties] = Field(
        default_factory=CodeAbilityMetaProperties,
        description="Assignment-specific properties"
    )

    @field_validator('description', mode='before')
    @classmethod
    def empty_list_to_none(cls, value):
        """Convert empty lists to None for description."""
        if isinstance(value, list) and len(value) == 0:
            return None
        return value


