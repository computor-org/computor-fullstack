import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent  / ".env.dev"
load_dotenv(env_path)

from ctutor_backend.database import get_db
from ctutor_backend.model.seeder import seed
from ctutor_backend.model.models import User, UserRole
from ctutor_backend.interface.tokens import encrypt_api_key
from ctutor_backend.database import get_db

def create_admin():
    with next(get_db()) as db:

        user = User()
        user.given_name = "Tea"
        user.family_name = "Pot"
        user.email = "tea.pot.drink"
        user.username = "admin"
        user.password = encrypt_api_key("admin")
        db.add(user)
        db.commit()

        user_role = UserRole()
        user_role.user_id = user.id

        user_role.role_id = "_admin"
        db.add(user_role)
        db.commit()

if __name__ == "__main__":
    # Optional: Base.metadata.create_all(engine) falls du Tabellen neu erzeugen willst
    seed()
    create_admin()