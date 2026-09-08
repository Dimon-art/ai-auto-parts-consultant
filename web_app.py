from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import find_parts_by_fitment
from partsapi_fitment import find_partsapi_fitment
from ai_assistant import ask_ai

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="AI Auto Parts Consultant")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class Query(BaseModel):
    make: str
    model: str
    year: int
    engine: str = ""
    part_request: str


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/query")
def query(data: Query):
    local_matches = find_parts_by_fitment(
        data.make,
        data.model,
        data.year,
        data.engine,
        data.part_request,
    )

    partsapi_matches = find_partsapi_fitment(
        data.make,
        data.model,
        data.year,
        data.engine,
        data.part_request,
    )

    # Для MVP PartsAPI является основным источником данных.
    # Локальные демонстрационные позиции не смешиваем
    # с подтвержденными PartsAPI артикулами.
    combined_matches = partsapi_matches or local_matches

    ai_answer = ""

    if partsapi_matches:
        ai_answer = ask_ai(
            partsapi_matches[0],
            data.make,
            data.model,
            data.year,
            data.engine,
            data.part_request,
        )
    elif local_matches:
        ai_answer = ask_ai(
            local_matches[0],
            data.make,
            data.model,
            data.year,
            data.engine,
            data.part_request,
        )

    result = {
        "matches": combined_matches,
        "ai_answer": ai_answer,
    }

    return JSONResponse(
        content=result,
        media_type="application/json; charset=utf-8",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8023)
