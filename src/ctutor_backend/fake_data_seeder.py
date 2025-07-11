#!/usr/bin/env python3
"""
Fake data seeder for the ComputingTutor database.
Generates realistic test data for development and testing.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Add the current directory to path to import models
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.sqlalchemy_models import *
from sqlalchemy_utils import Ltree

# Fake data generators
from faker import Faker
fake = Faker()

def create_db_session():
    """Create database session using environment variables."""
    postgres_url = os.environ.get('POSTGRES_URL', 'localhost')
    postgres_user = os.environ.get('POSTGRES_USER', 'postgres')
    postgres_password = os.environ.get('POSTGRES_PASSWORD', 'postgres_secret')
    postgres_db = os.environ.get('POSTGRES_DB', 'codeability_fresh')
    
    database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_url}/{postgres_db}"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def create_course_content_kinds(session):
    """Create course content kinds."""
    kinds = [
        {
            'id': 'assignment',
            'title': 'Assignment',
            'description': 'Programming assignments for students',
            'has_ascendants': False,
            'has_descendants': True,
            'submittable': True
        },
        {
            'id': 'lecture',
            'title': 'Lecture',
            'description': 'Lecture materials and slides',
            'has_ascendants': False,
            'has_descendants': True,
            'submittable': False
        },
        {
            'id': 'exercise',
            'title': 'Exercise',
            'description': 'Practice exercises',
            'has_ascendants': False,
            'has_descendants': True,
            'submittable': True
        },
        {
            'id': 'exam',
            'title': 'Exam',
            'description': 'Examinations and tests',
            'has_ascendants': False,
            'has_descendants': False,
            'submittable': True
        }
    ]
    
    for kind_data in kinds:
        kind = CourseContentKind(**kind_data)
        session.add(kind)
    
    print("✅ Created course content kinds")

def create_course_roles(session):
    """Create course roles."""
    roles = [
        {'id': '_student', 'title': 'Student', 'description': 'Course student'},
        {'id': '_tutor', 'title': 'Tutor', 'description': 'Course tutor/TA'},
        {'id': '_lecturer', 'title': 'Lecturer', 'description': 'Course lecturer/instructor'},
        {'id': '_admin', 'title': 'Administrator', 'description': 'Course administrator'}
    ]
    
    for role_data in roles:
        role = CourseRole(**role_data)
        session.add(role)
    
    print("✅ Created course roles")

def create_users(session, count=50):
    """Create fake users."""
    users = []
    
    for i in range(count):
        user = User(
            given_name=fake.first_name(),
            family_name=fake.last_name(),
            email=fake.unique.email(),
            username=fake.unique.user_name(),
            user_type='user',
            fs_number=1000 + i
        )
        session.add(user)
        users.append(user)
    
    session.flush()  # Get IDs
    print(f"✅ Created {count} users")
    return users

def create_organizations(session, users):
    """Create organizations."""
    organizations = []
    
    # Create a main university organization
    main_org = Organization(
        title="Example University",
        description="A leading institution for computing education",
        organization_type='organization',
        path=Ltree('university'),
        email='admin@university.edu',
        telephone='+1-555-123-4567',
        url='https://university.edu',
        locality='Example City',
        region='Example State',
        country='Example Country',
        created_by=random.choice(users).id
    )
    session.add(main_org)
    organizations.append(main_org)
    
    # Create departments
    departments = ['Computer Science', 'Information Systems', 'Software Engineering']
    for dept_name in departments:
        dept = Organization(
            title=f"Department of {dept_name}",
            description=f"The {dept_name} department",
            organization_type='organization',
            path=Ltree(f"university.{dept_name.lower().replace(' ', '_')}"),
            email=f'{dept_name.lower().replace(" ", ".")}@university.edu',
            created_by=random.choice(users).id
        )
        session.add(dept)
        organizations.append(dept)
    
    session.flush()
    print(f"✅ Created {len(organizations)} organizations")
    return organizations

def create_execution_backends(session, users):
    """Create execution backends."""
    backends = [
        {
            'type': 'python',
            'slug': 'python-3-11',
            'created_by': random.choice(users).id
        },
        {
            'type': 'java',
            'slug': 'java-17',
            'created_by': random.choice(users).id
        },
        {
            'type': 'cpp',
            'slug': 'gcc-11',
            'created_by': random.choice(users).id
        },
        {
            'type': 'matlab',
            'slug': 'matlab-2023a',
            'created_by': random.choice(users).id
        }
    ]
    
    execution_backends = []
    for backend_data in backends:
        backend = ExecutionBackend(**backend_data)
        session.add(backend)
        execution_backends.append(backend)
    
    session.flush()
    print(f"✅ Created {len(backends)} execution backends")
    return execution_backends

def create_course_families(session, organizations, users):
    """Create course families."""
    course_families = []
    
    cs_org = next(org for org in organizations if 'Computer Science' in org.title)
    
    families_data = [
        {'title': 'Programming Fundamentals', 'path': 'cs.programming'},
        {'title': 'Data Structures & Algorithms', 'path': 'cs.algorithms'},
        {'title': 'Software Engineering', 'path': 'cs.software_eng'},
        {'title': 'Machine Learning', 'path': 'cs.ml'}
    ]
    
    for family_data in families_data:
        family = CourseFamily(
            title=family_data['title'],
            description=f"Course family for {family_data['title']}",
            path=Ltree(family_data['path']),
            organization_id=cs_org.id,
            created_by=random.choice(users).id
        )
        session.add(family)
        course_families.append(family)
    
    session.flush()
    print(f"✅ Created {len(course_families)} course families")
    return course_families

def create_courses(session, course_families, organizations, users, execution_backends):
    """Create courses."""
    courses = []
    
    cs_org = next(org for org in organizations if 'Computer Science' in org.title)
    
    for family in course_families:
        # Create 2-3 courses per family
        for i in range(random.randint(2, 3)):
            year = random.choice(['2023', '2024', '2025'])
            semester = random.choice(['fall', 'spring', 'summer'])
            
            course = Course(
                title=f"{family.title} {year}",
                description=f"{family.title} course for {semester} {year}",
                path=Ltree(f"{family.path}.{year}_{semester}"),
                course_family_id=family.id,
                organization_id=cs_org.id,
                version_identifier=f"v{year}.{i+1}",
                created_by=random.choice(users).id
            )
            session.add(course)
            session.flush()  # Flush to get course ID
            courses.append(course)
            
            # Add execution backends to course
            for backend in random.sample(execution_backends, random.randint(1, 2)):
                course_backend = CourseExecutionBackend(
                    course_id=course.id,
                    execution_backend_id=backend.id
                )
                session.add(course_backend)
    
    session.flush()
    print(f"✅ Created {len(courses)} courses")
    return courses

def create_course_groups(session, courses, users):
    """Create course groups."""
    course_groups = []
    
    for course in courses:
        # Create 3-5 groups per course
        for i in range(random.randint(3, 5)):
            group = CourseGroup(
                title=f"Group {i+1}",
                description=f"Study group {i+1} for {course.title}",
                course_id=course.id,
                created_by=random.choice(users).id
            )
            session.add(group)
            course_groups.append(group)
    
    session.flush()
    print(f"✅ Created {len(course_groups)} course groups")
    return course_groups

def main():
    """Main seeder function."""
    session = create_db_session()
    
    try:
        print("🌱 Starting fake data seeding...")
        
        # Create base data
        create_course_content_kinds(session)
        create_course_roles(session)
        session.commit()
        
        # Create users and organizations
        users = create_users(session, 50)
        organizations = create_organizations(session, users)
        execution_backends = create_execution_backends(session, users)
        session.commit()
        
        # Create course structure
        course_families = create_course_families(session, organizations, users)
        courses = create_courses(session, course_families, organizations, users, execution_backends)
        course_groups = create_course_groups(session, courses, users)
        session.commit()
        
        print("🎉 Fake data seeding completed successfully!")
        print(f"Created:")
        print(f"  - {len(users)} users")
        print(f"  - {len(organizations)} organizations") 
        print(f"  - {len(execution_backends)} execution backends")
        print(f"  - {len(course_families)} course families")
        print(f"  - {len(courses)} courses")
        print(f"  - {len(course_groups)} course groups")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    main()