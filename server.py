import fastapi
import uvicorn

app = fastapi.FastAPI()


# {{REPLACE_ME}}


if __name__ == "__main__":
    uvicorn.run("server:app", port=8080, log_level="info")
