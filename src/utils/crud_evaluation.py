from typing import Optional, List, Dict
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.evaluation import Evaluation
from schemas.evaluation import EvaluationCreate, EvaluationUpdate
from .crud_base import CRUDBase


class CRUDEvaluation(CRUDBase[Evaluation, EvaluationCreate, EvaluationUpdate]):
    """CRUD операции для модели Evaluation"""

    async def create_evaluation(
        self,
        session: AsyncSession,
        obj_in: EvaluationCreate,
        evaluator_id: uuid.UUID
    ) -> Evaluation:
        """Создать оценку."""
        evaluation = Evaluation(
            **obj_in.model_dump(),
            evaluator_id=evaluator_id
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation, ["user", "evaluator", "task"])
        return evaluation

    async def get_by_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> List[Evaluation]:
        """Получить все оценки задачи."""
        result = await session.execute(
            select(Evaluation).options(
                selectinload(Evaluation.user),
                selectinload(Evaluation.evaluator),
                selectinload(Evaluation.task)
            ).where(Evaluation.task_id == task_id)
        )
        return result.scalars().all()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Evaluation]:
        """Получить все оценки пользователя."""
        result = await session.execute(
            select(Evaluation).options(
                selectinload(Evaluation.user),
                selectinload(Evaluation.evaluator),
                selectinload(Evaluation.task)
            ).where(
                Evaluation.user_id == user_id
            ).offset(skip).limit(limit).order_by(Evaluation.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_evaluator(
        self,
        session: AsyncSession,
        evaluator_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Evaluation]:
        """Получить все оценки, выставленные пользователем."""
        result = await session.execute(
            select(Evaluation).options(
                selectinload(Evaluation.user),
                selectinload(Evaluation.evaluator),
                selectinload(Evaluation.task)
            ).where(
                Evaluation.evaluator_id == evaluator_id
            ).offset(skip).limit(limit).order_by(Evaluation.created_at.desc())
        )
        return result.scalars().all()

    async def get_user_average_score(
        self,
        session: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[float]:
        """Получить среднюю оценку пользователя."""
        result = await session.execute(
            select(func.avg(Evaluation.score)).where(
                Evaluation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_statistics(
        self,
        session: AsyncSession,
        user_id: uuid.UUID
    ) -> Dict[str, any]:
        """Получить статистику оценок пользователя."""
        evaluations = await self.get_by_user(session, user_id, limit=1000)
        if not evaluations:
            return {
                "total": 0,
                "average": 0,
                "by_score": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        total = len(evaluations)
        scores = [e.score for e in evaluations]
        average = sum(scores) / total if total > 0 else 0
        by_score = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for score in scores:
            by_score[score] = by_score.get(score, 0) + 1
        return {
            "total": total,
            "average": round(average, 2),
            "by_score": by_score,
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0
        }

    async def check_existing_evaluation(
        self,
        session: AsyncSession,
        task_id: int,
        user_id: uuid.UUID
    ) -> Optional[Evaluation]:
        """Проверить, есть ли уже оценка для этой задачи и пользователя."""
        result = await session.execute(
            select(Evaluation).where(
                Evaluation.task_id == task_id,
                Evaluation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


evaluation_crud = CRUDEvaluation(Evaluation)
