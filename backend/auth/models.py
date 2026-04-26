import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(sa.String(120))
    username: Mapped[str] = mapped_column(sa.String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(sa.String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255))
    face_image_path: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
