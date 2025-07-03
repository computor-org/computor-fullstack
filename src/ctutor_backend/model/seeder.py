import os
import uuid
import random
from faker import Faker
from sqlalchemy import select
from sqlalchemy_utils import Ltree
from ctutor_backend.database import get_db
from ctutor_backend.model import User, Account, StudentProfile
from ctutor_backend.model import Organization, CourseFamily, Course
from ctutor_backend.model import CourseGroup, CourseMember
from ctutor_backend.model.models import CourseRole

fake = Faker()
Faker.seed(0)

NUM_USERS = 50

def create_user():
    return User(
        id=str(uuid.uuid4()),
        given_name=fake.first_name(),
        family_name=fake.last_name(),
        email=fake.unique.email(),
        username=fake.unique.user_name(),
        user_type='user'
    )

def create_account(user):
    return Account(
        id=str(uuid.uuid4()),
        provider='gitlab.testing.test',
        type='gitlab',
        provider_account_id=str(fake.unique.uuid4()),
        user_id=user.id
    )

def create_student_profile(user):
    return StudentProfile(
        id=str(uuid.uuid4()),
        student_id=str(fake.unique.random_int(min=100000, max=999999)),
        student_email=user.email,
        user_id=user.id
    )

def create_organization():
    company = fake.company()

    return Organization(
        id=str(uuid.uuid4()),
        title=company,
        description=fake.text(max_nb_chars=200),
        number=fake.unique.bothify(text="ORG-####"),
        email=fake.company_email(),
        telephone=fake.phone_number(),
        fax_number=fake.phone_number(),
        url=fake.url(),
        postal_code=fake.postcode(),
        street_address=fake.street_address(),
        locality=fake.city(),
        region=fake.state(),
        country=fake.country(),
        organization_type='organization',
        path=Ltree(company.lower().replace(" ","").replace("-","").replace(",",""))
    )

def create_course_family(org_id, org_path):
    path = fake.company().lower().replace(" ","").replace("-","").replace(",","")
    return CourseFamily(
        id=str(uuid.uuid4()),
        title=fake.catch_phrase(),
        description=fake.text(max_nb_chars=150),
        organization_id=org_id,
        path=Ltree(f"{org_path}.{path}")
    )

def create_course(org_id, cf_id, cf_path):
    path = fake.company().lower().replace(" ","").replace("-","").replace(",","")
    return Course(
        id=str(uuid.uuid4()),
        title=fake.bs().capitalize(),
        description=fake.text(max_nb_chars=150),
        organization_id=org_id,
        course_family_id=cf_id,
        path=Ltree(f"{cf_path}.{path}"),
        version_identifier=f"v{random.randint(1,5)}.{random.randint(0,9)}"
    )

def create_course_group(course_id):
    return CourseGroup(
        id=str(uuid.uuid4()),
        title=fake.word().capitalize() + " Group",
        description=fake.text(max_nb_chars=150),
        course_id=course_id
    )

def create_course_member(user_id, course_id, course_group_id, course_role_id):
    return CourseMember(
        id=str(uuid.uuid4()),
        user_id=user_id,
        course_id=course_id,
        course_group_id=course_group_id,
        course_role_id=course_role_id
    )

def seed():

    with next(get_db()) as db:
        users = []
        accounts = []
        profiles = []

        for _ in range(NUM_USERS):
            user = create_user()
            account = create_account(user)
            profile = create_student_profile(user)

            users.append(user)
            accounts.append(account)
            profiles.append(profile)
            
        db.add_all(users + accounts + profiles)
        db.commit()
        print(f"Seeded {NUM_USERS} users with accounts and student profiles.")

        orgs = []
        cfs = []
        courses = []

        for _ in range(random.randint(3, 10)):
            org = create_organization()
            orgs.append(org)
            db.add(org)
            db.flush()  # damit org.id verfügbar ist

            for _ in range(random.randint(1, 5)):
                cf = create_course_family(org.id, org.path)
                cfs.append(cf)
                db.add(cf)
                db.flush()

                for _ in range(random.randint(1, 4)):
                    course = create_course(org.id, cf.id, cf.path)
                    courses.append(course)
                    db.add(course)
        
        db.commit()

        users = db.query(User).filter(User.user_type == 'user').all()
        if len(users) < 50:
            print("⚠️  Not enough users for course member seeding. Skipping.")
            return

        # Lade die _student Rolle, nimm z.B. die erste passende
        student_role = db.execute(
            select(CourseRole).where(CourseRole.id == '_student')  # oder filter nach Name o.Ä.
        ).scalar_one_or_none()

        if not student_role:
            raise Exception("Missing course role with id '_student'")

        student_role_id = student_role.id

        all_courses = db.query(Course).all()
        group_count = 0
        member_count = 0

        available_user_ids_per_course = {
            course.id: set(user.id for user in users) for course in all_courses
        }

        for course in all_courses:
            available_user_ids = available_user_ids_per_course[course.id]
            
            # Erzeuge 1–2 Gruppen pro Kurs
            for _ in range(random.randint(1, 2)):
                group = CourseGroup(
                    id=str(uuid.uuid4()),
                    title=fake.bs().title(),
                    description=fake.text(),
                    course_id=course.id,
                    created_by=random.choice(users).id,
                    updated_by=random.choice(users).id,
                )
                db.add(group)
                db.flush()

                num_members = min(len(available_user_ids), random.randint(10, 20))
                if num_members == 0:
                    break
                member_user_ids = random.sample(list(available_user_ids), num_members)

                for user_id in member_user_ids:
                    member = CourseMember(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        course_id=course.id,
                        course_group_id=group.id,
                        course_role_id=student_role_id,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    db.add(member)
                    available_user_ids.remove(user_id) 


        db.commit()
        print(f"✅ Seeded {group_count} course groups and {member_count} course members.")
