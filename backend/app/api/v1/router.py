from fastapi import APIRouter

from app.api.v1 import admin, assessments, auth, health, me, metadata, occupations, questionnaires, recommendations, students

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(occupations.router)
api_router.include_router(metadata.router)
api_router.include_router(questionnaires.router)
api_router.include_router(assessments.router)
api_router.include_router(recommendations.router)
api_router.include_router(students.router)
api_router.include_router(admin.router)
