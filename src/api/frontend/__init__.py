from fastapi import APIRouter
from . import auth, dashboard, tasks, teams, meetings, profile, evaluations


router = APIRouter()

router.include_router(auth.router, tags=["frontend-auth"])
router.include_router(dashboard.router, tags=["frontend-dashboard"])
router.include_router(tasks.router, tags=["frontend-tasks"])
router.include_router(teams.router, tags=["frontend-teams"])
router.include_router(meetings.router, tags=["frontend-meetings"])
router.include_router(profile.router, tags=["frontend-profile"])
router.include_router(evaluations.router, tags=["frontend-evaluations"])
