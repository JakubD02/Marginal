from decimal import Decimal

import pytest

from marginal.calculations import (
    check_sales_share,
    get_sales_share_per_scenario,
    run_simulation,
)
from marginal.enums import CostCategory, Unit
from marginal.models import (
    FixedCost,
    Product,
    RecipeItem,
    SeasonalityFactor,
    TrafficAssumption,
)


class TestSalesShareValidation:
    """Tests for check_sales_share and get_sales_share_per_scenario."""

    def test_check_sales_share_valid_100_percent(self, session, sample_scenario):
        """Products summing to 1.0 should pass validation."""
        _add_product(session, sample_scenario, "A_first", 0.5)
        _add_product(session, sample_scenario, "B_second", 0.5)
        session.refresh(sample_scenario)

        assert check_sales_share(sample_scenario.products) is True

    def test_check_sales_share_below_100(self, session, sample_scenario):
        """Products summing below 1.0 should fail validation."""
        _add_product(session, sample_scenario, "A_first", 0.3)
        _add_product(session, sample_scenario, "B_second", 0.4)
        session.refresh(sample_scenario)

        assert check_sales_share(sample_scenario.products) is False

    def test_check_sales_share_above_100(self, session, sample_scenario):
        """Products summing above 1.0 should fail validation."""
        _add_product(session, sample_scenario, "A_first", 0.6)
        _add_product(session, sample_scenario, "B_second", 0.6)
        session.refresh(sample_scenario)

        assert check_sales_share(sample_scenario.products) is False

    def test_check_sales_share_tolerance(self, session, sample_scenario):
        """Small floating point errors should be tolerated (< 0.0001)."""
        _add_product(session, sample_scenario, "A_first", 0.33333)
        _add_product(session, sample_scenario, "B_second", 0.33333)
        _add_product(session, sample_scenario, "C_third", 0.33334)
        session.refresh(sample_scenario)

        assert check_sales_share(sample_scenario.products) is True

    def test_check_sales_share_empty_products(self):
        """Empty product list should fail (sum = 0, not 1)."""
        assert check_sales_share([]) is False

    def test_get_sales_share_sums_correctly(self, session, sample_scenario):
        """Sum should equal sum of individual shares."""
        _add_product(session, sample_scenario, "A", 0.2)
        _add_product(session, sample_scenario, "B", 0.3)
        _add_product(session, sample_scenario, "C", 0.5)
        session.refresh(sample_scenario)

        total = get_sales_share_per_scenario(sample_scenario.products)
        assert abs(total - Decimal("1.0")) < Decimal("0.0001")


class TestSimulationRequiresValidShares:
    """Simulation should refuse to run if shares don't sum to 100%."""

    def test_simulate_fails_when_shares_not_100(
        self, session, sample_scenario, sample_ingredient
    ):
        """Simulation should raise ValueError if shares don't sum to 1.0."""
        _add_product_with_recipe(session, sample_scenario, sample_ingredient, "A", 0.3)
        _add_product_with_recipe(session, sample_scenario, sample_ingredient, "B", 0.4)
        _add_traffic_and_seasonality(session, sample_scenario)
        session.refresh(sample_scenario)

        with pytest.raises(ValueError, match="100%"):
            run_simulation(sample_scenario)

    def test_simulate_succeeds_when_shares_sum_to_100(
        self, session, sample_scenario, sample_ingredient
    ):
        """Simulation should run when shares sum to 1.0."""
        _add_product_with_recipe(session, sample_scenario, sample_ingredient, "A", 0.5)
        _add_product_with_recipe(session, sample_scenario, sample_ingredient, "B", 0.5)
        _add_traffic_and_seasonality(session, sample_scenario)
        session.refresh(sample_scenario)

        result = run_simulation(sample_scenario)
        assert result is not None
        assert len(result.monthly_pnl) == 12


def _add_product(session, scenario, name, share):
    product = Product(
        scenario_id=scenario.id,
        name=name,
        price=Decimal("10.00"),
        category="drink",
        wastage_pct=0.0,
        expected_sales_share=share,
    )
    session.add(product)
    session.commit()
    return product


def _add_product_with_recipe(session, scenario, ingredient, name, share):
    product = _add_product(session, scenario, name, share)
    recipe = RecipeItem(
        product_id=product.id,
        ingredient_id=ingredient.id,
        quantity=7.0,
        unit=Unit.GRAM,
    )
    session.add(recipe)
    session.commit()
    return product


def _add_traffic_and_seasonality(session, scenario):
    session.add(
        TrafficAssumption(
            scenario_id=scenario.id,
            daily_customers=100,
            avg_products_per_customer=1.5,
        )
    )
    session.add(
        FixedCost(
            scenario_id=scenario.id,
            name="Rent",
            amount=Decimal("3000.00"),
            category=CostCategory.RENT,
        )
    )
    for month in range(1, 13):
        session.add(
            SeasonalityFactor(
                scenario_id=scenario.id,
                month=month,
                multiplier=1.0,
            )
        )
    session.commit()
