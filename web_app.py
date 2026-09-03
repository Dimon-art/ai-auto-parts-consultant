from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import find_parts
from ai_assistant import ask_ai


app = FastAPI(title="AI Auto Parts Consultant")

app.mount("/static", StaticFiles(directory="static"), name="static")


class Query(BaseModel):
    make: str
    model: str
    year: int
    engine: str = ""
    part_request: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>AI Auto Parts Consultant</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f4f6f5;
    color: #26332d;
    margin: 0;
}

.container {
    max-width: 900px;
    margin: 40px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

h1 {
    color: #155d3a;
}

input,
button {
    width: 100%;
    box-sizing: border-box;
    padding: 12px;
    margin: 7px 0 15px;
    border-radius: 8px;
    border: 1px solid #ccd5d0;
    font-size: 16px;
}

button {
    background: #155d3a;
    color: white;
    border: 0;
    cursor: pointer;
}

button:hover {
    background: #0f4b2e;
}

.result {
    margin-top: 20px;
    padding: 18px;
    background: #eef6f1;
    border-left: 4px solid #155d3a;
    border-radius: 8px;
}

.ai-result {
    margin-top: 20px;
    padding: 18px;
    background: #f1f5f3;
    border-left: 4px solid #26332d;
    border-radius: 8px;
}

.ai-result h3 {
    margin-top: 0;
    color: #155d3a;
}

.part {
    margin-bottom: 18px;
    padding-bottom: 15px;
    border-bottom: 1px solid #dfe6e2;
}

.part:last-child {
    border-bottom: none;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>AI Auto Parts Consultant</h1>

<p>
Подбор автозапчастей по автомобилю и двигателю
</p>

<label>Марка автомобиля</label>

<input
    id="make"
    placeholder="Volkswagen"
>

<label>Модель</label>

<input
    id="model"
    placeholder="Golf"
>

<label>Год выпуска</label>

<input
    id="year"
    type="number"
    placeholder="2018"
>

<label>Двигатель</label>

<input
    id="engine"
    placeholder="1.4 TSI"
>

<label>Какая деталь нужна</label>

<input
    id="part_request"
    placeholder="масляный фильтр"
>

<button id="searchButton">
    Найти запчасть
</button>

<div id="result"></div>

</div>

</div>

<script src="/static/app.js"></script>

</body>

</html>
"""


@app.post("/query")
def query(data: Query):

    matches = find_parts(
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
