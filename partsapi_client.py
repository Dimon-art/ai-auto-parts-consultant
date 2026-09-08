import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.partsapi.ru"


def _get(api_key_name, params):
    api_key = os.getenv(api_key_name)

    if not api_key:
        raise RuntimeError(f"{api_key_name} не найден в .env")

    response = requests.get(
        BASE_URL,
        params=params | {"key": api_key},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_makes(car_type="PC", lang=16):
    return _get(
        "PARTSAPI_GETMAKES_KEY",
        {
            "method": "getMakes",
            "carType": car_type,
            "lang": lang,
        },
    )


def get_models(make_id, car_type="PC", lang=16):
    return _get(
        "PARTSAPI_GETMODELS_KEY",
        {
            "method": "getModels",
            "carType": car_type,
            "makeId": make_id,
            "lang": lang,
        },
    )


def get_cars(make_id, model_id, car_type="PC"):
    return _get(
        "PARTSAPI_GETCARS_KEY",
        {
            "method": "getCars",
            "carType": car_type,
            "makeId": make_id,
            "modelId": model_id,
        },
    )


def get_search_tree(car_id, car_type="PC", lang=16):
    return _get(
        "PARTSAPI_GETSEARCHTREE_KEY",
        {
            "method": "getSearchTree",
            "carType": car_type,
            "carId": car_id,
            "lang": lang,
        },
    )


def get_articles(str_id, car_id, car_type="PC", lang=16):
    return _get(
        "PARTSAPI_GETARTICLES_KEY",
        {
            "method": "getArticles",
            "carType": car_type,
            "strId": str_id,
            "carId": car_id,
            "lang": lang,
        },
    )


def get_article(art_num, sup_id, lang=16):
    return _get(
        "PARTSAPI_GETARTICLE_KEY",
        {
            "method": "getArticle",
            "LANG": lang,
            "ART_NUM": art_num,
            "SUP_ID": sup_id,
        },
    )


def find_search_tree_node(tree, search_text):
    """
    Ищет узел дерева PartsAPI по названию детали.
    Возвращает первый подходящий узел или None.
    """
    needle = search_text.strip().lower()

    if not needle:
        return None

    def walk(nodes):
        for node in nodes or []:
            name = str(
                node.get("STR_NAME")
                or node.get("name")
                or node.get("NAME")
                or ""
            ).strip()

            if needle in name.lower():
                return node

            children = (
                node.get("children")
                or node.get("CHILDREN")
                or node.get("items")
                or []
            )

            found = walk(children)

            if found:
                return found

        return None

    return walk(tree)


def get_fitment_articles(car_id, part_name, car_type="PC", lang=16):
    """
    Полный PartsAPI-поток:

    CAR_ID
      -> SearchTree
      -> нужная группа детали
      -> STR_ID
      -> Articles
      -> подробные Article данные

    Возвращает только статьи, для которых удалось получить
    подробные данные через getArticle.
    """

    tree = get_search_tree(
        car_id=car_id,
        car_type=car_type,
        lang=lang,
    )

    node = find_search_tree_node(tree, part_name)

    if not node:
        return {
            "car_id": car_id,
            "part_name": part_name,
            "str_id": None,
            "articles": [],
        }

    str_id = (
        node.get("STR_ID")
        or node.get("str_id")
        or node.get("STRID")
    )

    if not str_id:
        return {
            "car_id": car_id,
            "part_name": part_name,
            "str_id": None,
            "articles": [],
        }

    articles = get_articles(
        str_id=str_id,
        car_id=car_id,
        car_type=car_type,
        lang=lang,
    )

    result = []

    for article in articles:
        art_num = (
            article.get("ART_NUM")
            or article.get("art_num")
            or article.get("ARTICLE_NUMBER")
            or article.get("article_number")
        )

        sup_id = (
            article.get("SUP_ID")
            or article.get("sup_id")
        )

        if not art_num or not sup_id:
            continue

        try:
            details = get_article(
                art_num=art_num,
                sup_id=sup_id,
                lang=lang,
            )
        except requests.RequestException:
            continue

        result.append(
            {
                "car_id": car_id,
                "str_id": str_id,
                "article": article,
                "details": details,
            }
        )

    return {
        "car_id": car_id,
        "part_name": part_name,
        "str_id": str_id,
        "articles": result,
    }