import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Lấy thông số kết nối DB từ biến môi trường
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "docintel")

# Driver asyncpg để hỗ trợ AsyncIO trong Python
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Khởi tạo Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True nếu muốn xem log các câu SQL raw bên dưới
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db_session():
    """Dependency Generator để lấy DB Session cho API sau này"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
