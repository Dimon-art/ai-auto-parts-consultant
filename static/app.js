const searchButton = document.getElementById("searchButton");

searchButton.addEventListener("click", searchParts);


async function searchParts() {

    const result = document.getElementById("result");

    result.innerHTML = `
        <div class="result">
            Ищу подходящие запчасти...
        </div>
    `;

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


        if (!response.ok) {
            throw new Error("HTTP error " + response.status);
        }


        const json = await response.json();


        if (!json.matches || !json.matches.length) {

            result.innerHTML = `
                <div class="result">
                    <b>Совпадение не найдено.</b>
                    <br><br>
                    Уточните автомобиль, двигатель
                    или название детали.
                </div>
            `;

            return;
        }


        const partsHtml = json.matches.map(part => {

            const car = [
                part.make,
                part.model,
                part.year_from && part.year_to
                    ? `${part.year_from}–${part.year_to}`
                    : ""
            ].filter(Boolean).join(" ");

            const engines = Array.isArray(part.engines)
                ? part.engines.map(escapeHtml).join(", ")
                : escapeHtml(part.engines || "—");

            return `

            <div class="part">

                <h3>${escapeHtml(part.name)}</h3>

                <dl class="part-meta">

                    <dt>OEM</dt>
                    <dd>${escapeHtml(part.oem || "—")}</dd>

                    <dt>Категория</dt>
                    <dd>${escapeHtml(part.category || "—")}</dd>

                    <dt>Автомобиль</dt>
                    <dd>${escapeHtml(car || "—")}</dd>

                    <dt>Двигатель</dt>
                    <dd>${engines || "—"}</dd>

                    <dt>Цена</dt>
                    <dd>${part.price != null ? `${escapeHtml(part.price)} EUR` : "—"}</dd>

                    <dt>Совместимость</dt>
                    <dd>${escapeHtml(part.fitment_note || "—")}</dd>

                    <dt>Примечания</dt>
                    <dd>${escapeHtml(part.notes || "—")}</dd>

                </dl>

            </div>

        `;
        }).join("");


        let aiHtml = "";


        if (json.ai_answer) {

            aiHtml = `

                <div class="ai-result">

                    <h3>AI-консультант</h3>

                    <div>
                        ${formatAIAnswer(json.ai_answer)}
                    </div>

                </div>

            `;
        }


        result.innerHTML = `

            <div class="result">

                <h2>
                    Найдено: ${json.matches.length}
                </h2>

                ${partsHtml}

            </div>

            ${aiHtml}

        `;

    }


    catch (error) {

        console.error(error);

        result.innerHTML = `

            <div class="result">

                <b>Ошибка соединения с сервером.</b>

                <br><br>

                ${escapeHtml(error.message)}

            </div>

        `;
    }
}


function formatAIAnswer(text) {

    return escapeHtml(text)
        .replace(/\r\n/g, "<br>")
        .replace(/\n/g, "<br>")
        .replace(/\r/g, "<br>");
}


function escapeHtml(text) {

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
