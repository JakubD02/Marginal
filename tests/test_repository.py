from decimal import Decimal

import pytest

from marginal.enums import CostCategory, Month, Unit
from marginal.repository import (
    add_fixed_cost,
    add_product,
    create_scenario,
    delete_fixed_cost,
    delete_product,
    delete_scenario,
    get_fixed_costs_by_scenario,
    get_product_by_name_in_scenario,
    get_products_by_scenario,
    get_scenario_by_name,
    get_scenario_with_all,
    get_seasonality_by_scenario,
    get_traffic_assumption_by_scenario,
    list_scenarios,
    set_seasonality_for_month,
    set_traffic_assumption,
    update_product,
    update_scenario,
)
from marginal.schemas import (
    FixedCostCreate,
    ProductCreate,
    ProductUpdate,
    ScenarioCreate,
    ScenarioUpdate,
    SeasonalityFactorCreate,
    TrafficAssumptionCreate,
)


class TestScenarioCRUD:
    def test_create_scenario(self, session):
        data = ScenarioCreate(
            name="Cafe Milano",
            currency="EUR",
            working_days_per_month=24,
        )
        scenario = create_scenario(session, data)

        assert scenario.id is not None
        assert scenario.name == "Cafe Milano"
        assert scenario.currency == "EUR"
        assert scenario.working_days_per_month == 24

    def test_get_scenario_by_name_found(self, session, sample_scenario):
        found = get_scenario_by_name(session, "Test Cafe")

        assert found is not None
        assert found.id == sample_scenario.id

    def test_get_scenario_by_name_not_found(self, session):
        found = get_scenario_by_name(session, "Nonexistent")

        assert found is None

    def test_list_scenarios_empty(self, session):
        scenarios = list_scenarios(session)

        assert scenarios == []

    def test_list_scenarios_multiple(self, session):
        create_scenario(session, ScenarioCreate(name="A_first", currency="PLN"))
        create_scenario(session, ScenarioCreate(name="B_second", currency="EUR"))

        scenarios = list_scenarios(session)

        assert len(scenarios) == 2

    def test_update_scenario(self, session, sample_scenario):
        data = ScenarioUpdate(currency="USD")
        updated = update_scenario(session, sample_scenario.id, data)

        assert updated.currency == "USD"
        assert updated.name == "Test Cafe"

    def test_delete_scenario(self, session, sample_scenario):
        result = delete_scenario(session, sample_scenario.id)

        assert result is True
        assert get_scenario_by_name(session, "Test Cafe") is None

    def test_get_scenario_with_all_loads_relations(
        self, session, full_scenario
    ):
        loaded = get_scenario_with_all(session, full_scenario.id)

        assert loaded is not None
        assert len(loaded.products) > 0
        assert len(loaded.fixed_costs) > 0
        assert loaded.traffic_assumption is not None
        assert len(loaded.seasonality_factors) == 12


class TestProductCRUD:
    """Tests for product operations within a scenario"""

    def test_add_product(self, session, sample_scenario):
        data = ProductCreate(
            name="Cappuccino",
            price=Decimal("12.00"),
            category="drink",
            wastage_pct=0.05,
        )
        product = add_product(session, sample_scenario.id, data)

        assert product.id is not None
        assert product.scenario_id == sample_scenario.id
        assert product.name == "Cappuccino"

    def test_get_product_by_name_found(self, session, sample_product, sample_scenario):
        found = get_product_by_name_in_scenario(
            session, sample_scenario.id, "Espresso"
        )

        assert found is not None
        assert found.id == sample_product.id

    def test_get_product_by_name_not_found(self, session, sample_scenario):
        found = get_product_by_name_in_scenario(
            session, sample_scenario.id, "Nonexistent"
        )

        assert found is None

    def test_get_products_by_scenario(self, session, sample_product, sample_scenario):
        products = get_products_by_scenario(session, sample_scenario.id)

        assert len(products) == 1
        assert products[0].id == sample_product.id

    def test_update_product(self, session, sample_product, sample_scenario):
        data = ProductUpdate(price=Decimal("15.00"))
        updated = update_product(session, sample_scenario.id, "Espresso", data)

        assert updated.price == Decimal("15.00")
        assert updated.name == "Espresso"

    def test_delete_product(self, session, sample_product, sample_scenario):
        result = delete_product(session, sample_scenario.id, "Espresso")

        assert result is True
        assert (
            get_product_by_name_in_scenario(session, sample_scenario.id, "Espresso")
            is None
        )


class TestFixedCostCRUD:
    def test_add_fixed_cost(self, session, sample_scenario):
        data = FixedCostCreate(
            name="Insurance",
            amount=Decimal("200.00"),
            category=CostCategory.INSURANCE,
        )
        cost = add_fixed_cost(session, sample_scenario.id, data)

        assert cost.id is not None
        assert cost.scenario_id == sample_scenario.id
        assert cost.amount == Decimal("200.00")

    def test_get_fixed_costs_by_scenario(self, session, sample_scenario):
        add_fixed_cost(
            session,
            sample_scenario.id,
            FixedCostCreate(
                name="Rent",
                amount=Decimal("3000.00"),
                category=CostCategory.RENT,
            ),
        )
        add_fixed_cost(
            session,
            sample_scenario.id,
            FixedCostCreate(
                name="Electricity",
                amount=Decimal("400.00"),
                category=CostCategory.UTILITIES,
            ),
        )

        costs = get_fixed_costs_by_scenario(session, sample_scenario.id)

        assert len(costs) == 2

    def test_delete_fixed_cost(self, session, sample_scenario):
        add_fixed_cost(
            session,
            sample_scenario.id,
            FixedCostCreate(
                name="Rent",
                amount=Decimal("3000.00"),
                category=CostCategory.RENT,
            ),
        )

        result = delete_fixed_cost(session, sample_scenario.id, "Rent")

        assert result is True
        costs = get_fixed_costs_by_scenario(session, sample_scenario.id)
        assert len(costs) == 0


class TestTrafficAssumption:
    def test_set_traffic_assumption(self, session, sample_scenario):
        """Setting traffic should create the assumption."""
        data = TrafficAssumptionCreate(
            daily_customers=150,
            avg_products_per_customer=2.5,
        )
        traffic = set_traffic_assumption(session, sample_scenario.id, data)

        assert traffic.daily_customers == 150
        assert traffic.avg_products_per_customer == 2.5

    def test_get_traffic_assumption(self, session, sample_scenario):
        set_traffic_assumption(
            session,
            sample_scenario.id,
            TrafficAssumptionCreate(
                daily_customers=100,
                avg_products_per_customer=1.5,
            ),
        )

        traffic = get_traffic_assumption_by_scenario(session, sample_scenario.id)

        assert traffic is not None
        assert traffic.daily_customers == 100


class TestSeasonality:
    def test_set_seasonality_for_month(self, session, sample_scenario):
        data = SeasonalityFactorCreate(month=Month.JULY, multiplier=2.5)
        factor = set_seasonality_for_month(session, sample_scenario.id, data)

        assert factor.month == Month.JULY
        assert factor.multiplier == 2.5

    def test_get_seasonality_by_scenario(self, session, sample_scenario):
        set_seasonality_for_month(
            session,
            sample_scenario.id,
            SeasonalityFactorCreate(month=Month.JULY, multiplier=2.5),
        )
        set_seasonality_for_month(
            session,
            sample_scenario.id,
            SeasonalityFactorCreate(month=Month.AUGUST, multiplier=2.0),
        )

        factors = get_seasonality_by_scenario(session, sample_scenario.id)

        assert len(factors) == 2