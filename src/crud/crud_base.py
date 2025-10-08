from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        id: Any,
        relationships: Optional[list] = None
    ) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if relationships:
            opts = []
            for rel in relationships:
                if isinstance(rel, str):
                    opts.append(selectinload(getattr(self.model, rel)))
                else:
                    opts.append(rel)
            query = query.options(*opts)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
        query = select(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def create(
        self,
        session: AsyncSession,
        obj_in: CreateSchemaType,
        **kwargs
    ) -> ModelType:
        obj_data = obj_in.model_dump()
        obj_data.update(kwargs)
        db_obj = self.model(**obj_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        session: AsyncSession,
        *,
        id: Any
    ) -> Optional[ModelType]:
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.commit()
        return obj

    async def count(
        self,
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        id: Any
    ) -> bool:
        query = select(func.count()).select_from(
            self.model).where(self.model.id == id)
        result = await session.execute(query)
        return result.scalar_one() > 0
