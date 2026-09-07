import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.partsapi.ru"


def get_makes(car_type="PC", lang=16):
    api_key = os.getenv("PARTSAPI_GETMAKES_KEY")

    if not api_key:
        raise RuntimeError("PARTSAPI_GETMAKES_KEY не найден в .env")

    response = requests.get(
        BASE_URL,
        params={
            "method": "getMakes",
            "key": api_key,
            "carType": car_type,
            "lang": lang,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()

def get_models(make_id, car_type="PC", lang=16):
    api_key = os.getenv("PARTSAPI_GETMODELS_KEY")

    if not api_key:
        raise RuntimeError("PARTSAPI_GETMODELS_KEY не найден в .env")

    response = requests.get(
        BASE_URL,
        params={
            "method": "getModels",
            "key": api_key,
            "carType": car_type,
            "makeId": make_id,
            "lang": lang,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()

def get_cars(make_id, model_id, car_type="PC"):
    api_key = os.getenv("PARTSAPI_GETCARS_KEY")

    if not api_key:
        raise RuntimeError("PARTSAPI_GETCARS_KEY не найден в .env")

    response = requests.get(
        BASE_URL,
        params={
            "method": "getCars",
            "key": api_key,
            "carType": car_type,
            "makeId": make_id,
            "modelId": model_id,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()

def get_search_tree(car_id, car_type="PC", lang=16):
    api_key = os.getenv("PARTSAPI_GETSEARCHTREE_KEY")

    if not api_key:
        raise RuntimeError("PARTSAPI_GETSEARCHTREE_KEY не найден в .env")

    response = requests.get(
        BASE_URL,
        params={
            "method": "getSearchTree",
            "key": api_key,
            "carType": car_type,
            "carId": car_id,
            "lang": lang,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_articles(str_id, car_id, car_type="PC", lang=16):
    api_key = os.getenv("PARTSAPI_GETARTICLES_KEY")

    if not api_key:
        raise RuntimeError("PARTSAPI_GETARTICLES_KEY not found in .env")

    response = requests.get(
        BASE_URL,
        params={
            "method": "getArticles",
            "key": api_key,
            "carType": car_type,
            "strId": str_id,
            "carId": car_id,
            "lang": lang,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()
