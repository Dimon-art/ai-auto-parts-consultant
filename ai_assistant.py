import os
import requests
from dotenv import load_dotenv

load_dotenv()

VSEGPT_URL = "https://api.vsegpt.ru/v1/chat/completions"


def ask_ai(part, make, model, year, engine, user_request):
    api_key = os.getenv("VSEGPT_API_KEY")

    if not api_key:
        return "ИИ временно недоступен: VSEGPT_API_KEY не найден."

    oem_numbers = part.get("oem_numbers") or ""
    ean_numbers = part.get("ean_numbers") or ""
    criteria = part.get("article_criteria") or ""

    prompt = f"""
Ты AI-консультант по автозапчастям.

Объясни пользователю результат, который уже найден каталогом PartsAPI.

ДАННЫЕ АВТОМОБИЛЯ:
Марка: {make}
Модель: {model}
Год: {year}
Двигатель: {engine or "не указан"}

ЗАПРОС КЛИЕНТА:
{user_request}

ДАННЫЕ ИЗ PARTSAPI:
Артикул: {part.get("article_number") or "нет данных"}
Бренд: {part.get("brand") or "нет данных"}
Группа детали: {part.get("product_group") or "нет данных"}
OEM: {oem_numbers or "нет данных"}
EAN: {ean_numbers or "нет данных"}
Критерии: {criteria or "нет данных"}
Статус: {part.get("status") or "нет данных"}

ПОДТВЕРЖДЕНИЕ СОВМЕСТИМОСТИ:
Источник: {part.get("fitment_source") or "нет данных"}
CAR_ID: {part.get("car_id") or "нет данных"}
STR_ID: {part.get("str_id") or "нет данных"}
Совместимость подтверждена каталогом: {part.get("fitment_confirmed")}

СТРОГИЕ ПРАВИЛА:

1. Используй только переданные данные.
2. Ничего не придумывай.
3. Не придумывай OEM, аналоги, размеры, производителей, цены или характеристики.
4. Не утверждай дополнительных свойств детали, которых нет в данных.
5. Учитывай, что совместимость подтверждена связью PartsAPI для выбранного автомобиля и категории детали.
6. Если нужной информации нет, напиши: "В каталоге нет данных."
7. Ответ должен быть коротким и понятным.
8. Ответ только на русском языке.

Формат:

Подходит:
[краткий вывод]

Артикул:
[артикул]

Бренд:
[бренд]

OEM:
[OEM или "В каталоге нет данных."]

Почему:
[краткое объяснение на основании данных PartsAPI]

Важно:
[только действительно необходимое замечание]
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты консультант по автозапчастям. "
                    "Работай только с переданными данными PartsAPI. "
                    "Никогда не выдумывай отсутствующую информацию."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0,
    }

    try:
        response = requests.post(
            VSEGPT_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("VseGPT error:", e)

        return (
            "ИИ временно недоступен. "
            "Данные найденных запчастей показаны из каталога PartsAPI."
        )
