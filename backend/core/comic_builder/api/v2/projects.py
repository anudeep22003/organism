from fastapi import APIRouter

from ...state.relational.schemas import ProjectCreateSchema

router = APIRouter(tags=["comic", "builder", "v2", "projects"])


@router.get("/projects")
async def get_all_projects_of_user() -> dict:
    return {"message": "Hello, World!"}


@router.post("/projects")
async def create_project(project_data: ProjectCreateSchema) -> dict:
    return {"message": "Hello, World!"}
