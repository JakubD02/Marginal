# scripts/seed.py
from decimal import Decimal

from database import get_session
from enums import CostCategory
from models import FixedCost, Scenario


with get_session() as session:
    scenario = Scenario(name="Ice cream parlor 59", currency="PLN")
    scenario.fixed_costs.extend([
        FixedCost(name="Rent", amount=Decimal("5000"), category=CostCategory.RENT),
        FixedCost(name="ZUS", amount=Decimal("1600"), category=CostCategory.ZUS),
        FixedCost(name="Energy", amount=Decimal("400"), category=CostCategory.UTILITIES),
    ])
    session.add(scenario)
    session.commit()