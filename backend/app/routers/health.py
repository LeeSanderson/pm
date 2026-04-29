from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def read_health() -> dict[str, str]:
  return {"status": "ok"}


@router.get("/hello")
def read_hello() -> dict[str, str]:
  return {"message": "Hello from FastAPI."}
