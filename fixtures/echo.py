from fastapi import APIRouter


router = APIRouter()


@router.get("/echo/{content}")
async def echo(content: str) -> str:
    return content
