from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app import load_catalog, find_matches

app = FastAPI(title="AI Auto Parts Consultant")
catalog = load_catalog()


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
    box-shadow: 0 4px 20px rgba(0,0,0,.08);
}

h1 {
    color: #155d3a;
}

input, button {
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

.part {
    margin-bottom: 18px;
}
</style>
</head>

<body>

<div class="container">
<div class="card">

<h1>AI Auto Parts Consultant</h1>

<p>Подбор автозапчастей по автомобилю и двигателю</p>

<label>Марка автомобиля</label>
<input id="make" placeholder="Volkswagen">

<label>Модель</label>
<input id="model" placeholder="Golf">

<label>Год выпуска</label>
<input id="year" type="number" placeholder="2018">

<label>Двигатель</label>
<input id="engine" placeholder="1.4 TSI">

<label>Какая деталь нужна</label>
<input id="part_request" placeholder="масляный фильтр">

<button onclick="searchParts()">Найти запчасть</button>

<div id="result"></div>

</div>
</div>

<script>
async function searchParts() {

    const result = document.getElementById("result");

    result.innerHTML = "Ищу подходящие запчасти...";

    const data = {
        make: document.getElementById("make").value,
        model: document.getElementById("model").value,
        year: Number(document.getElementById("year").value),
        engine: document.getElementById("engine").value,
        part_request: document.getElementById("part_request").value
    };

    try {

        const response = await fetch("/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const json = await response.json();

        if (!json.matches.length) {

            result.innerHTML =
                "Совпадение не найдено.<br>" +
                "Уточните автомобиль, двигатель или название детали.";

            return;
        }

        result.innerHTML = json.matches.map(part => `

            <div class="part">

                <h3>${part.name}</h3>

                <b>OEM:</b> ${part.oem}<br>
                <b>Категория:</b> ${part.category}<br>
                <b>Цена:</b> ${part.price} EUR<br>
                <b>Двигатели:</b> ${part.engines.join(", ")}<br>
                <b>Совместимость:</b> ${part.fitment_note}

            </div>

        `).join("");

    } catch (error) {

        result.innerHTML =
            "Ошибка соединения с сервером.";

    }
}
</script>

</body>
</html>
"""


@app.post("/query")
def query(data: Query):

    matches = find_matches(
        catalog,
        data.make,
        data.model,
        data.year,
        data.engine,
        data.part_request,
    )

    return {"matches": matches}


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8023
    )
