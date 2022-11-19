from fastapi import APIRouter


router = APIRouter()


@router.get("/{content}")
async def echo(content: str) -> str:
    return content
