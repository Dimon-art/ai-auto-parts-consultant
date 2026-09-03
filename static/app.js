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


        const partsHtml = json.matches.map(part => `

            <div class="part">

                <h3>${escapeHtml(part.name)}</h3>

                <b>OEM:</b>
                ${escapeHtml(part.oem)}
                <br>

                <b>Категория:</b>
                ${escapeHtml(part.category)}
                <br>

                <b>Цена:</b>
                ${part.price} EUR
                <br>

                <b>Двигатели:</b>
                ${part.engines.map(escapeHtml).join(", ")}
                <br>

                <b>Совместимость:</b>
                ${escapeHtml(part.fitment_note)}

            </div>

        `).join("");


        let aiHtml = "";


        if (json.ai_answer) {

            aiHtml = `

                <div class="ai-result">

                    <h3>🤖 AI-консультант</h3>

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