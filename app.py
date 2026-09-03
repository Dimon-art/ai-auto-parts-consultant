from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "catalog.json"


def load_catalog() -> list[dict]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def ask(prompt: str, required: bool = True) -> str:
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("Введите значение.")


def find_matches(catalog: list[dict], make: str, model: str, year: int, engine: str, part_request: str) -> list[dict]:
    make_n, model_n, engine_n = map(normalize, (make, model, engine))
    request_n = normalize(part_request)
    matches = []

    for part in catalog:
        vehicle_ok = (
            normalize(part["make"]) == make_n
            and normalize(part["model"]) == model_n
            and part["year_from"] <= year <= part["year_to"]
        )
        if not vehicle_ok:
            continue

        engine_ok = not engine_n or any(engine_n in normalize(e) for e in part.get("engines", []))
        request_ok = any(request_n in normalize(term) or normalize(term) in request_n for term in part.get("keywords", []))
        if engine_ok and request_ok:
            matches.append(part)

    return matches


def print_result(matches: list[dict], make: str, model: str, year: int, engine: str, request: str) -> None:
    if not matches:
        print("\nСовпадение не найдено.")
        print("Уточните двигатель, год выпуска или название детали.")
        return

    print(f"\nНайдено вариантов: {len(matches)}")
    for i, part in enumerate(matches, 1):
        print(f"\n{i}. {part['name']}")
        print(f"   OEM: {part['oem']}")
        print(f"   Категория: {part['category']}")
        print(f"   Автомобиль: {make} {model}, {year}")
        print(f"   Двигатели: {', '.join(part['engines'])}")
        print(f"   Цена демо-каталога: {part['price']} EUR")
        print(f"   Совместимость: {part['fitment_note']}")
        if part.get("notes"):
            print(f"   Примечание: {part['notes']}")


def main() -> None:
    print("=== AI Auto Parts Consultant ===")
    print("Локальный MVP-консультант по подбору автозапчастей.\n")
    catalog = load_catalog()

    while True:
        make = ask("Марка автомобиля: ")
        model = ask("Модель: ")
        year_raw = ask("Год выпуска: ")
        engine = ask("Двигатель (можно оставить пустым): ", required=False)
        request = ask("Какая деталь нужна: ")

        try:
            year = int(year_raw)
        except ValueError:
            print("Год должен быть числом, например 2018.\n")
            continue

        matches = find_matches(catalog, make, model, year, engine, request)
        print_result(matches, make, model, year, engine, request)

        again = input("\nНовый подбор? [y/N]: ").strip().lower()
        if again not in {"y", "yes", "д", "да"}:
            break
        print()


if __name__ == "__main__":
    main()
