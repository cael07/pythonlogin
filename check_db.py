from backend.database import SessionLocal
from backend.auth.models import User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, Username: {u.username}, ImagePath: {u.face_image_path}")
db.close()
