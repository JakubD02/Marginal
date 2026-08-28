from decimal import Decimal
from sqlalchemy import select

from database import get_session
from enums import CostCategory, Unit
from models import FixedCost, Ingredient, Product, RecipeItem, Scenario, TrafficAssumption

SCENARIO_NAME = "Ice cream parlor 59"

def seed():
    with get_session() as session:
        existing = session.execute(select(Scenario).where(Scenario.name == SCENARIO_NAME)).scalar()
        if existing:
            print("Removing existing scenario...")
            session.delete(existing)
            session.flush()

        scenario = Scenario(
            name=SCENARIO_NAME,
            currency="PLN",
        )

        # --- Scenario ---
        scenario.fixed_costs.extend(
            [
                FixedCost(name="Rent", amount=Decimal("3000"), category=CostCategory.RENT),
                FixedCost(name="ZUS", amount=Decimal("1500"), category=CostCategory.ZUS),
                FixedCost(
                    name="Energy", amount=Decimal("500"), category=CostCategory.UTILITIES
                ),
            ]
        )

        # --- Ingredients ---
        strawberries = Ingredient(name="Strawberries", purchase_price=10.00, purchase_unit=Unit.KG, unit_size=1.0)
        milk = Ingredient(name="Milk 3.2%", purchase_price=3.00, purchase_unit=Unit.LITER, unit_size=1.0)
        cream = Ingredient(name="30% Cream", purchase_price=15.00, purchase_unit=Unit.LITER, unit_size=1.0)
        sugar = Ingredient(name="Sugar", purchase_price=4.00, purchase_unit=Unit.KG, unit_size=1.0)
        milk_powder = Ingredient(name="Skimmed milk powder", purchase_price=12.00, purchase_unit=Unit.KG, unit_size=1.0)
        dextrose = Ingredient(name="Dextrose", purchase_price=6.0, purchase_unit=Unit.KG, unit_size=1.0)
        stabilizer = Ingredient(name="Ice cream stabilizer", purchase_price=50.00, purchase_unit=Unit.KG, unit_size=1.0)
        wafer = Ingredient(name="Ice cream wafer", purchase_price=0.40, purchase_unit=Unit.PIECE, unit_size=1.0)

        scenario.ingredients.extend([
            strawberries, milk, cream, sugar, milk_powder, dextrose, stabilizer, wafer
        ])

        # --- Products ---
        strawberry_scoop = Product(
            name="Strawberry ice cream scoop",
            price=Decimal("8"),
            category="food",
            wastage_pct = 0.08
        )

        scenario.products.append(strawberry_scoop)

        # --- Traffic assumption ---
        scenario.traffic_assumption = TrafficAssumption(
            daily_customers = 150,
            avg_products_per_customer=2.5
        )

        session.add(scenario)
        session.flush()

        strawberry_scoop.recipe_items.extend([
            RecipeItem(ingredient_id=strawberries.id, quantity=10.0, unit=Unit.GRAM),
            RecipeItem(ingredient_id=milk.id, quantity=23.75, unit=Unit.ML),
            RecipeItem(ingredient_id=cream.id, quantity=6.25,  unit=Unit.ML),
            RecipeItem(ingredient_id=sugar.id, quantity=5.0, unit=Unit.GRAM),
            RecipeItem(ingredient_id=milk_powder.id, quantity=2.5, unit=Unit.GRAM),
            RecipeItem(ingredient_id=dextrose.id, quantity=2.0, unit=Unit.GRAM),
            RecipeItem(ingredient_id=stabilizer.id, quantity=0.25, unit=Unit.GRAM),
            RecipeItem(ingredient_id=wafer.id, quantity=1.0, unit=Unit.PIECE),
        ])

if __name__ == "__main__":
    seed()