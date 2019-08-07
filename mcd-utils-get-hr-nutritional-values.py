#!/usr/local/bin/python3
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

base_domain: str = "https://mcdonalds.hr"
product_api_endpoint: str = f"{base_domain}/api/products/"
calculator_api_endpoint: str = f"{base_domain}/api/calculator_items/"

salt_sodium_content: float = 0.4

nutrition_mapping_table: Dict[str, str] = {
    "proteins": "Protein",
    "fats_saturated": "Saturated fat",
    "kj": "kJ",
    "carbohidrates": "Carbohydrates",
    "fibers": "Fiber",
    "kcal": "kcal",
    "fats": "Fat",
    "salt": "Sodium",
    "carbohidrates_sugar": "Sugars"
}

nutrition_unit_mapping_table: Dict[str, str] = {
    "proteins": "g",
    "fats_saturated": "g",
    "kj": "kJ",
    "carbohidrates": "g",
    "fibers": "g",
    "kcal": "kcal",
    "fats": "g",
    "salt": "g",
    "carbohidrates_sugar": "g"
}

allergen_mapping_table: Dict[str, str] = {
    "Jaja": "Eggs",
    "Mlijeko (uklju\u010duju\u0107i laktozu)": "Milk",
    "Celer": "Celery",
    "Senf": "Mustard",
    "Sjeme sezama": "Sesame seeds",
    "Sumporov dioksid": "Sulphur dioxide",
    "Gluten": "Gluten",
    "Riba": "Fish",
    "Orašasti plodovi": "Nuts",
    "Soja": "Soy",
    "Lupina": "Lupin"
}


def get_soup(url: str) -> BeautifulSoup:
    return BeautifulSoup(requests.get(url).content, "lxml")


def post_json(url: str, data: Dict) -> Dict:
    return requests.post(url, json=data).json()


def get_categories() -> List[Tuple[str, int]]:
    fat_soup: BeautifulSoup = get_soup(base_domain)

    data: Dict[str, int] = dict()

    category_tag: Tag
    for category_tag in fat_soup.find("div", {"class": "category_container"}).find_all("a"):
        category_name_tag: Tag = category_tag.find("h3")
        category_name: str = category_name_tag.text.strip()
        category_id: int = int(category_tag["id"].split("_")[-1])
        data[category_name] = category_id

    return [(x, y) for x, y in data.items()]


def get_category_data(category_id: int) -> Tuple[str, List[Tuple[str, str, int]]]:
    category_raw_data: Dict = post_json(product_api_endpoint, {
        "category_id": category_id,
        "allergens": []
    })

    category_data: Dict = category_raw_data["products"][0]

    # noinspection PyUnusedLocal
    category_name: str = category_data["name"]
    category_image_url: str = category_data["image"]

    products: List[Dict] = category_data["products"]

    return (category_image_url, [
        (product["name"], product["image"], int(product["id"]))
        for product
        in products
    ])


def get_product_data(product_id: int) -> Tuple[List[Tuple[str, str, float]], List[str]]:
    product_raw_data: Dict = post_json(calculator_api_endpoint, {
        "variant_id": product_id,
        "adding": True
    })

    product_data: Dict = product_raw_data["calculator_items"][0]
    product_allergen_data: List[Dict] = product_raw_data["calculator_items_alergens"]
    nutrition_data: Dict[str, List[float]] = product_data["nutritive"]

    nutrients: List[Tuple[str, str, float]] = [
        (
            nutrition_mapping_table[nutrition_item_name],
            nutrition_unit_mapping_table[nutrition_item_name],
            round(nutrition_values[0], 2)
            if nutrition_item_name != "salt"
            else round(nutrition_values[0] * salt_sodium_content, 3)
        )
        for nutrition_item_name, nutrition_values
        in nutrition_data.items()
    ]

    allergens: List[str] = [
        allergen_mapping_table[allergen_data["name"]]
        for allergen_data
        in product_allergen_data
    ]

    return nutrients, allergens


def main():
    for category_name, category_id in get_categories():
        category_image_url: str
        products: Tuple[str, str, int]

        category_image_url, products = get_category_data(category_id)

        print(f"{category_id} - {category_name} ({category_image_url}):")

        for product_name, product_image_url, product_id in products:
            product_nutrients: Dict[str, float]
            product_allergens: List[str]

            product_nutrients, product_allergens = get_product_data(product_id)

            product_allergen_string: str = ", ".join(product_allergens)

            print(f"\t{product_id} - {product_name} ({product_image_url}):")

            print(f"\t\tAllergens - {product_allergen_string}")

            print(f"\t\tNutrition:")

            product_nutrient_name: str
            product_nutrient_unit: str
            product_nutrient_value: float
            for product_nutrient_name, product_nutrient_unit, product_nutrient_value in product_nutrients:
                print(f"\t\t\t{product_nutrient_name} - {product_nutrient_value} {product_nutrient_unit}")


if __name__ == '__main__':
    main()
