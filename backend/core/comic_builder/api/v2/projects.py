from fastapi import APIRouter

router = APIRouter(tags=["comic", "builder", "v2", "projects"])


@router.get("/projects")
async def get_all_projects_of_user() -> dict:
    return {"message": "Hello, World!"}
