import fastapi
import uvicorn

app = fastapi.FastAPI()


# {{REPLACE_ME}}


if __name__ == "__main__":
    from pathlib import Path

    this_file = Path(__file__)
    import_name = this_file.name
    import_name = import_name[: -len(".py")]
    uvicorn.run(f"{import_name}:app", port=8080, log_level="info")
