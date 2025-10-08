from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.comment import TaskComment
from schemas.comment import CommentCreate, CommentUpdate
from .crud_base import CRUDBase


class CRUDComment(CRUDBase[TaskComment, CommentCreate, CommentUpdate]):
    async def create_comment(
        self,
        session: AsyncSession,
        obj_in: CommentCreate,
        author_id: uuid.UUID
    ) -> TaskComment:
        comment = TaskComment(
            **obj_in.model_dump(),
            author_id=author_id
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment, ["author", "task"])
        return comment

    async def get_by_task(
        self,
        session: AsyncSession,
        task_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskComment]:
        result = await session.execute(
            select(TaskComment).options(
                selectinload(TaskComment.author),
                selectinload(TaskComment.task)
            ).where(
                TaskComment.task_id == task_id
            ).order_by(
                TaskComment.created_at.desc()
            ).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_author(
        self,
        session: AsyncSession,
        author_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskComment]:
        result = await session.execute(
            select(TaskComment).options(
                selectinload(TaskComment.author),
                selectinload(TaskComment.task)
            ).where(
                TaskComment.author_id == author_id
            ).order_by(
                TaskComment.created_at.desc()
            ).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_by_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> int:
        return await self.count(session, filters={"task_id": task_id})


comment_crud = CRUDComment(TaskComment)
