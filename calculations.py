from decimal import Decimal

from sqlalchemy import select

from database import get_session
from models import Ingredient
from units import convert


def compute_unit_cost(product) -> Decimal:
    total = Decimal("0")

    for item in product.recipe_items:
        recipe_item_unit = item.quantity
        ingredient_unit = item.ingredient.purchase_unit
        ingredient_size = item.ingredient.unit_size
        ingredient_price = item.ingredient.purchase_price

        factor = convert(ingredient_size, ingredient_unit, item.unit) / recipe_item_unit
        factor_decimal = Decimal(str(factor))

        per_portion = ingredient_price / factor_decimal
        total += per_portion

    wastage_factor = Decimal("1") + Decimal(str(product.wastage_pct))
    total *= wastage_factor

    return total