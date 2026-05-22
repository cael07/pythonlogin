import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from typing import ClassVar
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
    role: Mapped[str] = mapped_column(sa.String(20), default="passenger")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Driver Verification fields
    license_number: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    license_image_path: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    or_renewal_date: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    or_image_path: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    cr_plate_number: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    cr_brand: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    cr_color: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    cr_model: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    cr_owner_name: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    cr_image_path: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    # Base64 image storage — stored directly in DB so images persist on Render.
    # Render's filesystem is ephemeral; PostgreSQL TEXT columns handle base64 fine.
    face_image_b64_db: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    license_image_b64_db: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    or_image_b64_db: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    cr_image_b64_db: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    @property
    def face_image_base64(self) -> str | None:
        return self.face_image_b64_db

    @property
    def license_image_base64(self) -> str | None:
        return self.license_image_b64_db

    @property
    def or_image_base64(self) -> str | None:
        return self.or_image_b64_db

    @property
    def cr_image_base64(self) -> str | None:
        return self.cr_image_b64_db


class Booking(Base):
    __tablename__ = "ride_bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    passenger_id: Mapped[int] = mapped_column(sa.ForeignKey("auth_users.id"))
    driver_id: Mapped[int | None] = mapped_column(sa.ForeignKey("auth_users.id"), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(20), default="pending") # pending, accepted, completed, cancelled
    pickup_lat: Mapped[float] = mapped_column(sa.Float)
    pickup_lng: Mapped[float] = mapped_column(sa.Float)
    dropoff_lat: Mapped[float] = mapped_column(sa.Float)
    dropoff_lng: Mapped[float] = mapped_column(sa.Float)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
