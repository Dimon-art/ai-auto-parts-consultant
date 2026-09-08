const CURRENT_YEAR = new Date().getFullYear();
const MAX_YEAR = CURRENT_YEAR + 1;
const MIN_YEAR = 1950;
const MAX_PARTS = 5;
const SEARCH_BUTTON_LABEL = "🔎 Найти запчасть";
const SEARCH_BUTTON_LOADING = "Поиск…";

const VEHICLE_CATALOG = {
    Volkswagen: {
        Golf: {
            yearFrom: 2013,
            yearTo: 2020,
            engines: ["1.0L TSI 6MT FWD (110 HP)", "1.0L TSI 7AT FWD (110 HP)", "1.4 TSI", "1.5 TSI", "2.0 TDI"]
        },
        Passat: {
            yearFrom: 2015,
            yearTo: 2023,
            engines: ["1.5 TSI", "2.0 TDI"]
        },
        Tiguan: {
            yearFrom: 2016,
            yearTo: 2024,
            engines: ["1.0 TSI", "1.4 TSI", "1.5 TSI", "2.0 TDI"]
        }
    },
    Nissan: {
        Qashqai: {
            yearFrom: 2014,
            yearTo: 2021,
            engines: ["1.2 DIG-T", "1.3 DIG-T", "1.5 dCi"]
        },
        "X-Trail": {
            yearFrom: 2014,
            yearTo: 2022,
            engines: ["1.6 DIG-T", "1.7 dCi", "2.0"]
        }
    },
    Toyota: {
        Corolla: {
            yearFrom: 2013,
            yearTo: 2024,
            engines: ["1.6 Dual VVT-i", "1.8 Hybrid", "2.0 Hybrid"]
        },
        RAV4: {
            yearFrom: 2013,
            yearTo: 2024,
            engines: ["2.0", "2.5 Hybrid"]
        }
    },
    BMW: {
        "3 Series": {
            yearFrom: 2012,
            yearTo: 2024,
            engines: ["320i", "320d", "330i"]
        }
    },
    Audi: {
        A4: {
            yearFrom: 2012,
            yearTo: 2023,
            engines: ["1.4 TFSI", "2.0 TFSI", "2.0 TDI"]
        }
    }
};

// Детали из текущей MVP-базы (не отправлять имя категории в part_request)
const CATEGORY_PARTS = {
    "Фильтры": ["Масляный фильтр", "Воздушный фильтр"],
    "Тормозная система": ["Передние тормозные колодки"]
};

const makeSelect = document.getElementById("make");
const modelSelect = document.getElementById("model");
const yearSelect = document.getElementById("year");
const engineSelect = document.getElementById("engine");
const partInput = document.getElementById("part_request");
const searchForm = document.getElementById("searchForm");
const searchButton = document.getElementById("searchButton");
const resultEl = document.getElementById("result");
const vinModal = document.getElementById("vinModal");
const vinInput = document.getElementById("vinInput");
const vinMessage = document.getElementById("vinMessage");
const vinCheckButton = document.getElementById("vinCheckButton");

let toastTimer = null;
let activeCategoryBtn = null;

initVehicleSelects();
bindEvents();


function initVehicleSelects() {
    const makes = Object.keys(VEHICLE_CATALOG).sort();

    for (const make of makes) {
        makeSelect.appendChild(createOption(make, make));
    }
}


function bindEvents() {
    makeSelect.addEventListener("change", onMakeChange);
    modelSelect.addEventListener("change", onModelChange);
    yearSelect.addEventListener("change", onYearChange);
    partInput.addEventListener("input", function () {
        clearFieldError("part_request");
    });

    searchForm.addEventListener("submit", function (event) {
        event.preventDefault();
        searchParts();
    });

    document.querySelectorAll(".category-btn").forEach(function (btn) {
        btn.addEventListener("click", function (event) {
            event.preventDefault();

            const category = (btn.getAttribute("data-category") || "").trim();
            if (!category) {
                return;
            }

            setActiveCategory(btn);

            const parts = CATEGORY_PARTS[category];
            if (!parts || !parts.length) {
                removeCategoryPartPicker();
                showToast("В текущем MVP для этой категории данных пока нет.");
                return;
            }

            if (parts.length === 1) {
                removeCategoryPartPicker();
                applyPartRequest(parts[0]);
                return;
            }

            showCategoryPartPicker(parts);
        });
    });

    resultEl.addEventListener("click", function (event) {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }

        if (target.matches("[data-action='compare']")) {
            showToast("Сравнение будет доступно в следующей версии.");
            return;
        }

        if (target.matches("[data-action='save']")) {
            showToast("Сохранение будет доступно в следующей версии.");
            return;
        }

        if (target.matches("[data-action='vin']")) {
            openVinModal();
        }
    });

    vinModal.querySelectorAll("[data-close-modal]").forEach(function (el) {
        el.addEventListener("click", closeVinModal);
    });

    vinCheckButton.addEventListener("click", function () {
        vinMessage.hidden = false;
        vinMessage.textContent =
            "VIN-подбор будет подключён к каталогу в следующей версии.";
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !vinModal.hidden) {
            closeVinModal();
        }
    });
}


function setActiveCategory(btn) {
    if (activeCategoryBtn) {
        activeCategoryBtn.classList.remove("is-active");
    }
    btn.classList.add("is-active");
    activeCategoryBtn = btn;
}


function applyPartRequest(partName) {
    partInput.value = "";
    partInput.value = partName;
    clearFieldError("part_request");
    partInput.focus();
}


function removeCategoryPartPicker() {
    const existing = document.getElementById("categoryPartPicker");
    if (existing) {
        existing.remove();
    }
}


function showCategoryPartPicker(parts) {
    removeCategoryPartPicker();

    const picker = document.createElement("div");
    picker.id = "categoryPartPicker";
    picker.setAttribute("role", "group");
    picker.setAttribute("aria-label", "Выбор детали");
    picker.style.display = "flex";
    picker.style.flexWrap = "wrap";
    picker.style.gap = "8px";
    picker.style.margin = "0 0 12px";

    const label = document.createElement("p");
    label.textContent = "Выберите деталь:";
    label.style.margin = "0";
    label.style.width = "100%";
    label.style.fontSize = "0.85rem";
    label.style.fontWeight = "600";
    label.style.color = "#667069";
    picker.appendChild(label);

    parts.forEach(function (partName) {
        const partBtn = document.createElement("button");
        partBtn.type = "button";
        partBtn.textContent = partName;
        partBtn.style.padding = "8px 12px";
        partBtn.style.border = "1px solid #d4dbd6";
        partBtn.style.borderRadius = "8px";
        partBtn.style.background = "#ffffff";
        partBtn.style.color = "#243028";
        partBtn.style.font = "inherit";
        partBtn.style.fontSize = "0.88rem";
        partBtn.style.fontWeight = "600";
        partBtn.style.cursor = "pointer";

        partBtn.addEventListener("click", function () {
            applyPartRequest(partName);
            removeCategoryPartPicker();
        });

        picker.appendChild(partBtn);
    });

    searchButton.parentNode.insertBefore(picker, searchButton);
}


function onMakeChange() {
    clearFieldError("make");
    resetSelect(modelSelect, "Выберите модель", true);
    resetSelect(yearSelect, "Выберите год", true);
    resetSelect(engineSelect, "Необязательно", true);

    const make = makeSelect.value;
    if (!make || !VEHICLE_CATALOG[make]) {
        return;
    }

    const models = Object.keys(VEHICLE_CATALOG[make]).sort();
    modelSelect.disabled = false;

    for (const model of models) {
        modelSelect.appendChild(createOption(model, model));
    }
}


function onModelChange() {
    clearFieldError("model");
    resetSelect(yearSelect, "Выберите год", true);
    resetSelect(engineSelect, "Необязательно", true);

    const entry = getSelectedVehicleEntry();
    if (!entry) {
        return;
    }

    const from = Math.max(MIN_YEAR, entry.yearFrom);
    const to = Math.min(MAX_YEAR, entry.yearTo);
    yearSelect.disabled = false;

    for (let year = to; year >= from; year -= 1) {
        yearSelect.appendChild(createOption(String(year), String(year)));
    }
}


function onYearChange() {
    clearFieldError("year");
    resetSelect(engineSelect, "Необязательно", true);

    const entry = getSelectedVehicleEntry();
    if (!entry || !yearSelect.value) {
        return;
    }

    engineSelect.disabled = false;
    for (const engine of entry.engines) {
        engineSelect.appendChild(createOption(engine, engine));
    }
}


function getSelectedVehicleEntry() {
    const make = makeSelect.value;
    const model = modelSelect.value;
    if (!make || !model || !VEHICLE_CATALOG[make] || !VEHICLE_CATALOG[make][model]) {
        return null;
    }
    return VEHICLE_CATALOG[make][model];
}


function createOption(value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
}


function resetSelect(selectEl, placeholder, disabled) {
    selectEl.innerHTML = "";
    selectEl.appendChild(createOption("", placeholder));
    selectEl.disabled = Boolean(disabled);
    selectEl.value = "";
}


async function searchParts() {
    if (!validateForm()) {
        return;
    }

    const make = makeSelect.value.trim();
    const model = modelSelect.value.trim();
    const year = Number(yearSelect.value);
    const engine = engineSelect.value.trim();
    const partRequest = partInput.value.trim();

    setLoading(true);
    renderLoadingState(partRequest);

    const data = {
        make: make,
        model: model,
        year: year,
        engine: engine,
        part_request: partRequest
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
        renderResults(json, partRequest);
    } catch (error) {
        console.error(error);
        resultEl.innerHTML = `
            <div class="dialog">
                <div class="status-banner error">
                    Не удалось получить ответ сервера. Попробуйте ещё раз через минуту.
                </div>
            </div>
        `;
    } finally {
        setLoading(false);
    }
}


function validateForm() {
    let ok = true;

    const make = makeSelect.value.trim();
    const model = modelSelect.value.trim();
    const yearRaw = yearSelect.value.trim();
    const partRequest = partInput.value.trim();

    clearAllErrors();

    if (!make) {
        setFieldError("make", "Выберите марку автомобиля.");
        ok = false;
    }

    if (!model) {
        setFieldError("model", "Выберите модель.");
        ok = false;
    }

    if (!yearRaw) {
        setFieldError("year", "Выберите год выпуска.");
        ok = false;
    } else {
        const year = Number(yearRaw);
        if (!Number.isInteger(year) || year < MIN_YEAR || year > MAX_YEAR) {
            setFieldError(
                "year",
                "Укажите год от " + MIN_YEAR + " до " + MAX_YEAR + "."
            );
            ok = false;
        }
    }

    if (!partRequest) {
        setFieldError("part_request", "Укажите, какая деталь нужна.");
        ok = false;
    }

    return ok;
}


function setFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorEl = document.getElementById(fieldId + "-error");
    const wrapper = field && field.closest(".field");

    if (wrapper) {
        wrapper.classList.add("has-error");
    }
    if (errorEl) {
        errorEl.hidden = false;
        errorEl.textContent = message;
    }
}


function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorEl = document.getElementById(fieldId + "-error");
    const wrapper = field && field.closest(".field");

    if (wrapper) {
        wrapper.classList.remove("has-error");
    }
    if (errorEl) {
        errorEl.hidden = true;
        errorEl.textContent = "";
    }
}


function clearAllErrors() {
    ["make", "model", "year", "engine", "part_request"].forEach(clearFieldError);
}


function setLoading(isLoading) {
    searchButton.disabled = isLoading;
    searchButton.textContent = isLoading ? SEARCH_BUTTON_LOADING : SEARCH_BUTTON_LABEL;
}


function renderLoadingState(partRequest) {
    resultEl.innerHTML = `
        <div class="dialog">
            <div class="bubble bubble-user">
                <p class="bubble-label">Пользователь</p>
                <p class="bubble-text">Нужен(на): ${escapeHtml(partRequest)}</p>
            </div>
            <div class="bubble bubble-ai">
                <p class="bubble-label">AI</p>
                <p class="bubble-text bubble-loading">
                    Проверяю совместимость и ищу подходящие варианты<span class="dots"></span>
                </p>
            </div>
        </div>
    `;
}


function renderResults(json, partRequest) {
    const matches = Array.isArray(json.matches) ? json.matches.slice(0, MAX_PARTS) : [];
    const userBubble = `
        <div class="bubble bubble-user">
            <p class="bubble-label">Пользователь</p>
            <p class="bubble-text">Нужен(на): ${escapeHtml(partRequest)}</p>
        </div>
    `;

    if (!matches.length) {
        resultEl.innerHTML = `
            <div class="dialog">
                ${userBubble}
                <div class="bubble bubble-ai">
                    <p class="bubble-label">AI</p>
                    <p class="bubble-text">
                        Точного совпадения пока не найдено. Проверьте марку, модель, год, двигатель или уточните название детали. Для точного подбора используйте VIN.
                    </p>
                </div>
            </div>
        `;
        return;
    }

    const aiText = (json.ai_answer && String(json.ai_answer).trim())
        ? formatAIAnswer(json.ai_answer)
        : escapeHtml(
            "Я нашёл подходящие варианты. Перед заказом рекомендую подтвердить совместимость по VIN."
        );

    const partsHtml = matches.map(renderPartCard).join("");

    resultEl.innerHTML = `
        <div class="dialog">
            ${userBubble}
            <div class="bubble bubble-ai">
                <p class="bubble-label">AI</p>
                <div class="bubble-text">${aiText}</div>
            </div>
            <div class="status-banner">
                Найдено вариантов: ${matches.length}${json.matches.length > MAX_PARTS ? " (показаны первые " + MAX_PARTS + ")" : ""}
            </div>
            <div class="parts-grid">
                ${partsHtml}
            </div>
        </div>
    `;
}


function renderPartCard(part) {
    const articleNumber = part.article_number || "—";
    const brand = part.brand || "—";
    const productGroup = part.product_group || "Запчасть";
    const oem = part.oem_numbers || "—";
    const engine = part.engine || "—";

    const criteria = part.article_criteria || "";

    const fitment = escapeHtml(
        part.fitment_confirmed
            ? "Совместимость подтверждена каталогом PartsAPI для выбранного автомобиля и детали."
            : "Предварительная совместимость — требуется проверка VIN."
    );

    const icon = isFilterOrEnginePart({
        category: productGroup,
        name: productGroup
    }) ? "⚙" : "🚘";

    return `
        <article class="part-card">
            <div class="part-card-header">
                <div class="part-icon" aria-hidden="true">${icon}</div>
                <div>
                    <h3>${escapeHtml(productGroup)}</h3>
                    <p class="part-category">${escapeHtml(brand)}</p>
                </div>
            </div>

            <dl class="part-meta">
                <dt>Артикул</dt>
                <dd>${escapeHtml(articleNumber)}</dd>

                <dt>Бренд</dt>
                <dd>${escapeHtml(brand)}</dd>

                <dt>OEM</dt>
                <dd>${escapeHtml(oem)}</dd>

                <dt>Двигатель</dt>
                <dd>${escapeHtml(engine)}</dd>
            </dl>

            ${criteria ? `
            <div class="fitment-note">
                <strong>Характеристики:</strong>
                ${escapeHtml(criteria)}
            </div>
            ` : ""}

            <div class="fitment-note">
                <strong>Совместимость:</strong> ${fitment}
            </div>

            <div class="part-actions">
                <button type="button" data-action="compare">Сравнить</button>
                <button type="button" data-action="save">Сохранить</button>
                <button type="button" class="btn-vin" data-action="vin">Проверить по VIN</button>
            </div>
        </article>
    `;
}
function buildFitmentText(note) {
    const raw = String(note || "").trim();
    if (!raw) {
        return escapeHtml(
            "Предварительная совместимость — требуется проверка VIN. Подтвердите совместимость по VIN перед заказом."
        );
    }

    const lower = raw.toLowerCase();
    const alreadyCautious =
        lower.includes("vin") ||
        lower.includes("провер") ||
        lower.includes("сверк") ||
        lower.includes("предварит");

    if (alreadyCautious) {
        return escapeHtml(raw) +
            " " +
            escapeHtml("Предварительная совместимость — подтвердите совместимость по VIN.");
    }

    return escapeHtml(raw) +
        " " +
        escapeHtml("Предварительная совместимость — требуется проверка VIN.");
}


function isFilterOrEnginePart(part) {
    const category = String(part.category || "").toLowerCase();
    const name = String(part.name || "").toLowerCase();
    return (
        category.includes("фильтр") ||
        category.includes("двигател") ||
        name.includes("фильтр") ||
        name.includes("свеч")
    );
}


function openVinModal() {
    vinMessage.hidden = true;
    vinMessage.textContent = "";
    vinInput.value = "";
    vinModal.hidden = false;
    vinInput.focus();
}


function closeVinModal() {
    vinModal.hidden = true;
}


function showToast(message) {
    let toast = document.getElementById("appToast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "appToast";
        toast.className = "toast";
        toast.setAttribute("role", "status");
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("is-visible");

    if (toastTimer) {
        clearTimeout(toastTimer);
    }

    toastTimer = setTimeout(function () {
        toast.classList.remove("is-visible");
    }, 2400);
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
