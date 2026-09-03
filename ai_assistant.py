import os
import requests
from dotenv import load_dotenv

load_dotenv()

VSEGPT_URL = "https://api.vsegpt.ru/v1/chat/completions"


def ask_ai(part, make, model, year, engine, user_request):
    api_key = os.getenv("VSEGPT_API_KEY")

    if not api_key:
        return "ИИ временно недоступен: VSEGPT_API_KEY не найден."

    prompt = f"""
Ты AI-консультант по автозапчастям.

Твоя задача — только объяснить пользователю результат,
который уже найден локальным каталогом.

ДАННЫЕ АВТОМОБИЛЯ:
Марка: {make}
Модель: {model}
Год: {year}
Двигатель: {engine or "не указан"}

ЗАПРОС КЛИЕНТА:
{user_request}

ДАННЫЕ ИЗ КАТАЛОГА:
Название детали: {part["name"]}
OEM: {part["oem"]}
Категория: {part["category"]}
Цена: {part["price"]} EUR
Поддерживаемые двигатели: {", ".join(part["engines"])}
Совместимость: {part["fitment_note"]}

СТРОГИЕ ПРАВИЛА:

1. Используй ТОЛЬКО данные из блока "ДАННЫЕ ИЗ КАТАЛОГА".
2. Ничего не придумывай.
3. Не добавляй характеристики детали, которых нет в каталоге.
4. Не придумывай артикулы, аналоги, размеры, производителей или цены.
5. Не утверждай совместимость, если она прямо не следует из данных каталога.
6. Если какой-либо информации недостаточно, напиши:
   "В каталоге нет данных."
7. Не используй свои знания об автомобилях вместо данных каталога.
8. Обязательно укажи OEM из каталога.
9. Ответ должен быть коротким и понятным.
10. Ответ на русском языке.

Формат ответа:

Подходит:
[краткий вывод только по данным каталога]

OEM:
[OEM из каталога]

Почему:
[объяснение только по данным каталога]

Важно:
[что необходимо проверить, если это следует из данных каталога]
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
                    "Работай только с переданными данными каталога. "
                    "Никогда не выдумывай отсутствующую информацию. "
                    "Если данных недостаточно, скажи: "
                    "\"В каталоге нет данных.\""
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
            "Данные найденной запчасти показаны из каталога."
        )