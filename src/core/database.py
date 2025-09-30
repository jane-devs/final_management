from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.environment == "development"
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_async_session():
    """Получение асинхронной сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session
