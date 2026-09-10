from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from marginal.enums import CostCategory, Month, Unit
from marginal.models import (
    Base,
    FixedCost,
    Ingredient,
    Product,
    RecipeItem,
    Scenario,
    SeasonalityFactor,
    TrafficAssumption,
)


@pytest.fixture
def session():
    """Fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def sample_scenario(session):
    scenario = Scenario(
        name="Test Cafe",
        currency="PLN",
        working_days_per_month=22,
    )
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario


@pytest.fixture
def sample_ingredient(session, sample_scenario):
    ingredient = Ingredient(
        scenario_id=sample_scenario.id,
        name="Coffee beans",
        purchase_price=Decimal("25.00"),
        purchase_unit=Unit.KG,
        unit_size=1.0,
    )
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    return ingredient


@pytest.fixture
def sample_product(session, sample_scenario, sample_ingredient):
    product = Product(
        scenario_id=sample_scenario.id,
        name="Espresso",
        price=Decimal("10.00"),
        category="drink",
        wastage_pct=0.0,
        expected_sales_share=1.0,
    )
    session.add(product)
    session.flush()

    recipe_item = RecipeItem(
        product_id=product.id,
        ingredient_id=sample_ingredient.id,
        quantity=7.0,
        unit=Unit.GRAM,
    )
    session.add(recipe_item)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture
def full_scenario(session, sample_scenario, sample_product):
    fixed_cost = FixedCost(
        scenario_id=sample_scenario.id,
        name="Rent",
        amount=Decimal("3000.00"),
        category=CostCategory.RENT,
    )
    session.add(fixed_cost)

    traffic = TrafficAssumption(
        scenario_id=sample_scenario.id,
        daily_customers=100,
        avg_products_per_customer=1.5,
    )
    session.add(traffic)

    for month in Month:
        factor = SeasonalityFactor(
            scenario_id=sample_scenario.id,
            month=month,
            multiplier=1.0,
        )
        session.add(factor)

    session.commit()
    session.refresh(sample_scenario)
    return sample_scenario
