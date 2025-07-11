# Database Migration Analysis and SQLAlchemy Model Gaps

## Overview
This document provides a comprehensive analysis of the PostgreSQL migration files (V1.000-V1.018) and identifies gaps between the database schema and the current SQLAlchemy models.

## Migration File Analysis

### V1.000 - Base Extensions and Functions
**Extensions:**
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `ltree` - Hierarchical tree-like structures
- `citext` - Case-insensitive text

**Custom Types:**
- `ctutor_color` enum: red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose

**PostgreSQL Functions:**
- `ctutor_valid_label(TEXT)` - Validates labels with pattern `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
- `ctutor_update_timestamps()` - Trigger function for managing created_at/updated_at
- `ctutor_prevent_builtin_deletion()` - Prevents deletion of builtin entities

### V1.001 - Interface Tables (Schema Pattern)
Creates an `interfaces` schema with inheritance tables:
- `interfaces.string_id` - For string-based primary keys
- `interfaces.resource` - Base resource pattern (id, version, timestamps, created_by, updated_by, properties)
- `interfaces.archivable` - Adds archived_at timestamp
- `interfaces.title_description` - Adds title and description fields
- `interfaces.slugged` - Extends title_description with slug field
- `interfaces.number` - Adds number field
- `interfaces.contact` - Contact information fields
- `interfaces.avatar` - Avatar color and image
- `interfaces.address` - Address fields

**Key Finding:** These are template tables for PostgreSQL table inheritance, not actual data tables.

### V1.002 - Authentication Tables
**Tables:**
- `user` - Inherits from interfaces.number, resource, archivable
  - Special features: auth_token encryption trigger, conditional constraints for token users
  - Unique indexes on username, email, number (when not archived)
- `profile` - User profile with avatar support
- `student_profile` - Student-specific information
- `account` - External authentication providers
- `session` - User sessions with IP tracking

**Missing in SQLAlchemy:**
- `auth_token` field in User model (exists in DB as encrypted field)
- `db` user_type enum value (SQLAlchemy only has 'user' and 'token')
- Password encryption trigger logic
- Conditional unique indexes based on archived_at

### V1.003 - Organizations
**Tables:**
- `organization` - Hierarchical organization structure using ltree
  - Complex inheritance from multiple interface tables
  - Self-referential foreign key using ltree paths
  - Computed column `parent_path` for hierarchy navigation
  - Triggers for path validation and cascade updates

**Missing in SQLAlchemy:**
- `parent_path` computed column (commented out in model)
- Self-referential relationship for parent/child organizations
- Trigger logic for path validation and cascade operations

### V1.004 - Course Families
**Tables:**
- `course_family` - Groups related courses within an organization
  - Uses ltree for hierarchical paths
  - Unique constraint on (organization_id, path)

### V1.005 - Courses
**Tables:**
- `course` - Individual courses within families
  - Trigger to auto-set organization_id from course_family
  - Hierarchical path structure

### V1.006 - Course Groups
**Tables:**
- `course_group` - Groups within courses (e.g., lab sections)
  - Unique constraints on (course_id, title) and (course_id, id)

### V1.007 - Course Roles
**Tables:**
- `course_role` - Predefined roles: _owner, _maintainer, _study_assistant, _student
  - Uses string_id inheritance pattern

### V1.008 - Course Members
**Tables:**
- `course_member` - User membership in courses
  - Constraint: students must have a course_group_id
  - Composite foreign key to course_group

### V1.009 - Execution Backends
**Tables:**
- `execution_backend` - Test execution systems
  - Slug validation constraint

### V1.010 - Course Execution Backends
**Tables:**
- `course_execution_backend` - Links courses to execution backends
  - Composite primary key (course_id, execution_backend_id)

**Missing in SQLAlchemy:**
- This is a many-to-many relationship table with additional fields

### V1.011 - Course Content Kinds
**Tables:**
- `course_content_kind` - Types of content (assignment, unit, folder, quiz)
  - Flags for hierarchy and submission capability

### V1.012 - Course Content Types
**Tables:**
- `course_content_type` - Course-specific content type configurations
  - Links to course_content_kind
  - Includes color customization

### V1.013 - Course Contents
**Tables:**
- `course_content` - Actual course content items
  - Hierarchical structure with ltree paths
  - Trigger to enforce max_group_size based on submittable content
  - Position field for ordering

**Missing in SQLAlchemy:**
- Trigger logic for max_group_size validation

### V1.014 - Submission Groups
**Tables:**
- `course_submission_group` - Groups for collaborative submissions
  - Triggers to validate submittable content
  - Auto-set course_id from course_content

### V1.015 - Submission Group Members
**Tables:**
- `course_submission_group_member` - Members of submission groups
  - Multiple unique constraints to prevent duplicates
  - Triggers to auto-set fields from related tables

### V1.016 - Results
**Tables:**
- `result` - Test/submission results
  - Complex unique constraints for versioning
  - Trigger to set course_content_type_id

**Missing in SQLAlchemy:**
- Unique constraint on (course_member_id, course_content_id, version_identifier)

### V1.017 - User Roles and Groups
**Tables:**
- `role` - System-wide roles with builtin flag
- `user_role` - User-role assignments
- `role_claim` - Claims/permissions for roles
- `group` - User groups (fixed/dynamic types)
- `user_group` - User-group memberships
- `group_claim` - Claims for groups

**Missing in SQLAlchemy:**
- `role_claim` table
- `group_claim` table
- Validation triggers for group types
- `ctutor_valid_slug()` function usage

### V1.018 - Messages and Indexes
**Tables:**
- `codeability_message` - Course messaging system
- `codeability_message_read` - Read receipts for messages

**Missing in SQLAlchemy:**
- Both message tables are completely missing
- All the performance indexes created in this migration

## Critical Gaps in SQLAlchemy Models

### 1. Missing Tables
- `role_claim` - Permission claims for roles
- `group_claim` - Permission claims for groups  
- `codeability_message` - Messaging system
- `codeability_message_read` - Message read tracking

### 2. Missing Fields
- `User.auth_token` - Encrypted authentication token
- `User.db` enum value for user_type
- `Organization.parent_path` - Computed column for hierarchy
- Trigger update timestamps on many tables

### 3. Missing PostgreSQL Features
- Table inheritance from interfaces schema
- Conditional unique indexes (e.g., unique when not archived)
- Computed columns
- Trigger functions for:
  - Password/token encryption
  - Timestamp management
  - Cascade updates for hierarchical data
  - Field validation
  - Auto-population of related fields

### 4. Missing Constraints
- Check constraints using custom validation functions
- Conditional constraints based on other fields
- Complex foreign key relationships with ltree paths

### 5. Missing Indexes
- GIST indexes for ltree path searches
- Numerous performance indexes from V1.018
- Conditional unique indexes

## Recommendations

### High Priority
1. Add missing tables (messages, claims)
2. Implement conditional unique constraints in SQLAlchemy
3. Add missing fields and enum values
4. Implement computed columns where needed

### Medium Priority
1. Add all missing indexes for performance
2. Implement validation at the model level to match DB constraints
3. Document trigger behaviors in model docstrings

### Low Priority
1. Consider using SQLAlchemy events to replicate trigger logic
2. Evaluate if table inheritance pattern should be reflected in models
3. Add model-level path validation for ltree fields

## Special Considerations

### PostgreSQL-Specific Features
- **ltree**: Used extensively for hierarchical data (organizations, courses, content)
- **Table Inheritance**: Interface pattern not directly supported by SQLAlchemy
- **Computed Columns**: Need special handling in SQLAlchemy
- **Conditional Constraints**: Require custom validators or hybrid properties

### Security Features
- Password/token encryption at database level
- Row-level security through archived_at pattern
- Audit trail via created_by/updated_by fields

### Performance Optimizations
- GIST indexes for hierarchical queries
- Partial indexes for active records
- Composite indexes for common query patterns