from decimal import Decimal

from sqlalchemy import select

from database import get_session
from enums import CostCategory, Unit
from models import FixedCost, Ingredient, Product, RecipeItem, Scenario

with get_session() as session:
    scenario = Scenario(name="Ice cream test", currency="PLN")
    scenario.fixed_costs.append(
        FixedCost(name="Rent", amount=Decimal(5000), category=CostCategory.RENT)
    )

    base = Ingredient(
        name="Vanilla base",
        purchase_price=Decimal(15),
        purchase_unit=Unit.KG,
        unit_size=1.0,
    )
    scenario.ingredients.append(base)

    scoop = Product(name="Scoop", price=Decimal(9), category="lody", wastage_pct=0.05)
    scenario.products.append(scoop)

    session.add(scenario)
    session.flush()  # it is necessarily to get id

    scoop.recipe_items.append(
        RecipeItem(ingredient_id=base.id, quantity=80.0, unit=Unit.GRAM)
    )

with get_session() as session:
    scenario = session.execute(
        select(Scenario).where(Scenario.name == "Ice cream test")
    ).scalar_one()

    print(f"Scenario: {scenario.name}")
    print(f"Currency: {scenario.currency}")
    print(f"Cost: {[(c.name, c.amount) for c in scenario.fixed_costs]}")
    print(f"Products: {[p.name for p in scenario.products]}")
    for product in scenario.products:
        for item in product.recipe_items:
            print(
                f"  {product.name}: {item.quantity}{item.unit} {item.ingredient.name}"
            )
