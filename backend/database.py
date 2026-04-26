from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_url = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'auth.db')}")

# Support Render's 'postgres://' format and convert to async driver
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)

DATABASE_URL = _url

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    try:
        async with engine.begin() as conn:
            from .auth.models import User  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        print("DATABASE: Tables initialized successfully.")
    except Exception as e:
        print(f"DATABASE ERROR during init: {str(e)}")

async def check_db_health():
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
        return True
    except:
        return False
