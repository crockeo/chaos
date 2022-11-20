from fastapi import APIRouter


router = APIRouter()


@router.get("/hello_world")
async def hello_world() -> str:
    return "Hello world!"


@router.get("/hello/{name}")
async def hello_person(name: str) -> str:
    return f"Hello {name}! I hope you're doing well."
