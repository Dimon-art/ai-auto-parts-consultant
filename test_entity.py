import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.parts-index.com"


def test_entity(code, brand=None, language="ru"):
    api_key = os.getenv("PARTS_CATALOGS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "PARTS_CATALOGS_API_KEY не найден в .env"
        )

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
    }

    params = {
        "code": code,
        "language": language,
    }

    if brand:
        params["brand"] = brand

    print("=" * 60)
    print("Тест Parts Index API")
    print("=" * 60)
    print(f"Артикул: {code}")
    print(f"Бренд:   {brand}")
    print()

    response = requests.get(
        f"{BASE_URL}/v1/entities",
        headers=headers,
        params=params,
        timeout=30,
    )

    print("HTTP:", response.status_code)
    print()

    try:
        data = response.json()
    except ValueError:
        print("Ответ не является JSON:")
        print(response.text)
        return

    print("Ответ API:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if response.status_code == 200:
        print()
        print("✅ ДОСТУП К ИНФОРМАЦИИ О ДЕТАЛИ ПОЛУЧЕН")
    elif response.status_code == 403:
        print()
        print("❌ Доступ запрещён.")
        print("API-ключ пока не имеет необходимого права info.")
    else:
        print()
        print("⚠️ API вернул другой статус.")


if __name__ == "__main__":
    test_entity(
        code="W 940/5",
        brand="MANN-FILTER",
        language="ru",
    )