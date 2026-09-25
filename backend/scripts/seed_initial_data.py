"""Bootstrap script — run ONCE against an empty database.

Creates:
  - the SHIFT project
  - a default department list (editable afterwards by the Admin — nothing here
    is hardcoded into application logic, it's just starting data)
  - the first Admin user, from SEED_ADMIN_* environment variables

Usage (from backend/):
    python -m scripts.seed_initial_data
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.department import Department
from app.models.enums import RoleEnum
from app.models.project import Project
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_DEPARTMENTS = ["BD", "MKT", "Logistics", "Finance", "Corporate"]


def run() -> None:
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == RoleEnum.ADMIN).first()
        if existing_admin:
            print(f"An Admin user already exists ({existing_admin.email}). Aborting to avoid duplicates.")
            return

        project = db.query(Project).filter(Project.name == "SHIFT").first()
        if not project:
            project = Project(name="SHIFT")
            db.add(project)
            db.flush()
            print(f"Created project: {project.name}")

        for dept_name in DEFAULT_DEPARTMENTS:
            exists = (
                db.query(Department)
                .filter(Department.project_id == project.id, Department.name == dept_name)
                .first()
            )
            if not exists:
                db.add(Department(name=dept_name, project_id=project.id))
                print(f"Created department: {dept_name}")

        admin = User(
            full_name=settings.SEED_ADMIN_NAME,
            email=settings.SEED_ADMIN_EMAIL,
            password_hash=pwd_context.hash(settings.SEED_ADMIN_PASSWORD),
            role=RoleEnum.ADMIN,
            department_id=None,
            manager_id=None,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Created Admin user: {admin.email}")
        print("IMPORTANT: log in and change this password immediately.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
