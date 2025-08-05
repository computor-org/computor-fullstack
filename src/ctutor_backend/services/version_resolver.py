"""
Version constraint resolution service.

Handles semantic version constraint resolution for example dependencies.
"""

import re
from typing import List, Optional
from packaging import version
from sqlalchemy.orm import Session

from ..model.example import Example, ExampleVersion


class VersionResolver:
    """Resolves version constraints to specific example versions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def resolve_constraint(self, example_slug: str, constraint: Optional[str]) -> Optional[ExampleVersion]:
        """
        Resolve version constraint to a specific ExampleVersion.
        
        Args:
            example_slug: The hierarchical slug/identifier of the example
            constraint: Version constraint string (e.g., '>=1.2.0', '^2.1.0', '1.0.0')
                       If None, returns latest version
        
        Returns:
            ExampleVersion that satisfies the constraint, or None if not found
        """
        # Find the example by identifier
        example = self.db.query(Example).filter(
            Example.identifier == example_slug
        ).first()
        
        if not example:
            return None
        
        # Get all versions for this example
        all_versions = self.db.query(ExampleVersion).filter(
            ExampleVersion.example_id == example.id
        ).order_by(ExampleVersion.version_number.desc()).all()
        
        if not all_versions:
            return None
        
        # If no constraint specified, return latest version
        if not constraint:
            return all_versions[0]
        
        # Parse and resolve constraint
        return self._resolve_constraint_against_versions(constraint, all_versions)
    
    def _resolve_constraint_against_versions(self, constraint: str, versions: List[ExampleVersion]) -> Optional[ExampleVersion]:
        """
        Resolve version constraint against a list of available versions.
        
        Args:
            constraint: Version constraint string
            versions: List of ExampleVersion objects (should be sorted by version_number desc)  
        
        Returns:
            First version that satisfies constraint, or None
        """
        try:
            # Parse constraint
            if constraint.startswith('>='):
                min_version = version.parse(constraint[2:])
                for v in reversed(versions):  # Start from oldest to get minimum satisfying version
                    if version.parse(v.version_tag) >= min_version:
                        return v
                        
            elif constraint.startswith('<='):
                max_version = version.parse(constraint[2:])
                for v in versions:  # Start from newest
                    if version.parse(v.version_tag) <= max_version:
                        return v
                        
            elif constraint.startswith('>'):
                min_version = version.parse(constraint[1:])
                for v in reversed(versions):
                    if version.parse(v.version_tag) > min_version:
                        return v
                        
            elif constraint.startswith('<'):
                max_version = version.parse(constraint[1:])
                for v in versions:
                    if version.parse(v.version_tag) < max_version:
                        return v
                        
            elif constraint.startswith('^'):
                # Compatible version range (same major version)
                target_version = version.parse(constraint[1:])
                target_major = target_version.major
                
                for v in reversed(versions):
                    v_parsed = version.parse(v.version_tag)
                    if (v_parsed.major == target_major and 
                        v_parsed >= target_version):
                        return v
                        
            elif constraint.startswith('~'):
                # Patch-level compatibility
                target_version = version.parse(constraint[1:])
                target_major = target_version.major
                target_minor = target_version.minor
                
                for v in reversed(versions):
                    v_parsed = version.parse(v.version_tag)
                    if (v_parsed.major == target_major and 
                        v_parsed.minor == target_minor and
                        v_parsed >= target_version):
                        return v
                        
            elif constraint.startswith('=='):
                # Exact version match
                exact_version = constraint[2:]
                for v in versions:
                    if v.version_tag == exact_version:
                        return v
                        
            else:
                # No operator prefix - treat as exact match
                for v in versions:
                    if v.version_tag == constraint:
                        return v
                        
        except Exception:
            # If parsing fails, fall back to string comparison
            for v in versions:
                if v.version_tag == constraint:
                    return v
        
        return None
    
    def resolve_multiple_constraints(self, constraints: List[tuple]) -> List[ExampleVersion]:
        """
        Resolve multiple version constraints.
        
        Args:
            constraints: List of (example_slug, version_constraint) tuples
            
        Returns:
            List of resolved ExampleVersion objects
        """
        resolved = []
        for slug, constraint in constraints:
            version_obj = self.resolve_constraint(slug, constraint)
            if version_obj:
                resolved.append(version_obj)
        
        return resolved