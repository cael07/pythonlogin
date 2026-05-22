from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'auth.db')}")

# Fix Render's 'postgres://' for SQLAlchemy 2.0
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)

DATABASE_URL = _url

# Use simple engine like in inventory project
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        from .auth.models import User, Booking  # noqa: F401

        # Reset database for testing (drops only tables defined in this app)
        # print("DATABASE: Resetting auth_users table for testing...")
        # Base.metadata.drop_all(bind=engine)

        Base.metadata.create_all(bind=engine)

        with engine.connect() as conn:
            # All columns to auto-migrate (safe: silently ignored if column already exists)
            new_cols = [
                # Driver text metadata
                ("license_number",       "TEXT"),
                ("license_image_path",   "TEXT"),
                ("or_renewal_date",      "TEXT"),
                ("or_image_path",        "TEXT"),
                ("cr_plate_number",      "TEXT"),
                ("cr_brand",             "TEXT"),
                ("cr_color",             "TEXT"),
                ("cr_model",             "TEXT"),
                ("cr_owner_name",        "TEXT"),
                ("cr_image_path",        "TEXT"),
                # Base64 image columns stored in DB (persists on Render PostgreSQL)
                ("face_image_b64_db",    "TEXT"),
                ("license_image_b64_db", "TEXT"),
                ("or_image_b64_db",      "TEXT"),
                ("cr_image_b64_db",      "TEXT"),
            ]
            for col_name, col_type in new_cols:
                try:
                    conn.execute(text(f"ALTER TABLE auth_users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"DATABASE: Added column {col_name} to auth_users.")
                except Exception:
                    pass  # Column already exists — safe to ignore

        print("DATABASE: Tables initialized successfully.")
    except Exception as e:
        print(f"DATABASE ERROR during init: {str(e)}")

def check_db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DATABASE HEALTH CHECK FAILED: {str(e)}")
        return False
