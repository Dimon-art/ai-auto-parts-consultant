import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.parts-index.com"


def get_catalogs(language="ru"):
    api_key = os.getenv("PARTS_CATALOGS_API_KEY")

    if not api_key:
        raise RuntimeError("PARTS_CATALOGS_API_KEY не найден в .env")

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
    }

    response = requests.get(
        f"{BASE_URL}/v1/catalogs",
        headers=headers,
        params={"language": language},
        timeout=30,
    )

    print("HTTP:", response.status_code)
    print("Response:", response.text[:1000])

    response.raise_for_status()

    return response.json()


def get_catalog_entities(
    catalog_id="parts_to",
    language="ru",
    page=1,
    limit=10,
):
    api_key = os.getenv("PARTS_CATALOGS_API_KEY")

    if not api_key:
        raise RuntimeError("PARTS_CATALOGS_API_KEY не найден в .env")

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
    }

    response = requests.get(
        f"{BASE_URL}/v1/catalogs/{catalog_id}/entities",
        headers=headers,
        params={
            "language": language,
            "page": page,
            "limit": limit,
        },
        timeout=30,
    )

    print("Entities HTTP:", response.status_code)
    print("Entities response:", response.text[:3000])

    response.raise_for_status()

    return response.json()
def get_entity_by_code(code, brand=None, language="ru"):
    api_key = os.getenv("PARTS_CATALOGS_API_KEY")

    if not api_key:
        raise RuntimeError("PARTS_CATALOGS_API_KEY не найден в .env")

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

    response = requests.get(
        f"{BASE_URL}/v1/entities",
        headers=headers,
        params=params,
        timeout=30,
    )

    print("Entity HTTP:", response.status_code)
    print("Entity response:")
    print(response.text[:5000])

    response.raise_for_status()

    return response.json()
def get_entity_by_code(code, brand=None, language="ru"):
    api_key = os.getenv("PARTS_CATALOGS_API_KEY")

    if not api_key:
        raise RuntimeError("PARTS_CATALOGS_API_KEY не найден в .env")

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

    response = requests.get(
        f"{BASE_URL}/v1/entities",
        headers=headers,
        params=params,
        timeout=30,
    )

    print("Entity HTTP:", response.status_code)
    print("Entity response:")
    print(response.text[:5000])

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    entity = get_entity_by_code(
        code="W 940/5",
        brand="MANN-FILTER",
        language="ru",
    )

    print("Entity:", entity)