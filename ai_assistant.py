"""AI-консультант для подбора автозапчастей (DeepSeek API)."""
import os
import requests

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
TIMEOUT = 30


def _get_api_key() -> str | None:
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("VSEGPT_API_KEY")


def _build_prompt(part: dict, make: str, model: str, year: int, engine: str) -> str:
    name = part.get("name", "")
    oem = part.get("oem", "")
    fitment = part.get("fitment_note", "")
    engines = ", ".join(part.get("engines", []))
    return (
        f"Ты — консультант по автозапчастям. Клиент ищет деталь для автомобиля.\n\n"
        f"Автомобиль: {make} {model}, {year} г., двигатель {engine}\n"
        f"Запрос клиента: {name}\n"
        f"Найденная позиция:\n"
        f"  - Название: {name}\n"
        f"  - OEM: {oem}\n"
        f"  - Двигатели: {engines}\n"
        f"  - Примечание: {fitment}\n\n"
        f"Дай короткое объяснение (2–4 предложения) на русском:\n"
        f"1. Почему эта деталь подходит.\n"
        f"2. На что обратить внимание при покупке.\n"
        f"Без воды, по делу."
    )


def ask_ai(part: dict, make: str, model: str, year: int, engine: str = "") -> str:
    api_key = _get_api_key()
    if not api_key:
        return "ИИ временно недоступен: DEEPSEEK_API_KEY не найден."

    prompt = _build_prompt(part, make, model, year, engine)
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Ты краткий технический консультант по автозапчастям."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.HTTPError as e:
        return f"ИИ временно недоступен: ошибка API ({e.response.status_code})."
    except Exception as e:
        print("DeepSeek error:", e)
        return "ИИ временно недоступен. Попробуйте позже."