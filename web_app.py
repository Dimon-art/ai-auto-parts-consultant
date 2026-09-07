from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import find_parts_by_fitment
#from db import find_parts
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

    matches = find_parts_by_fitment(
        data.make,
        data.model,
        data.year,
        data.engine,
        data.part_request,
    )

    ai_answer = ""

    if matches:
        ai_answer = ask_ai(
            matches[0],
            data.make,
            data.model,
            data.year,
            data.engine,
            data.part_request,
        )

    return {
        "matches": matches,
        "ai_answer": ai_answer,
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8023,
    )
