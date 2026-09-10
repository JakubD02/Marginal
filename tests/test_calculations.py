from decimal import Decimal

from marginal.calculations import run_simulation
from marginal.enums import CostCategory, Month
from marginal.models import FixedCost, SeasonalityFactor, TrafficAssumption


class TestSimulation:
    def test_simulation_returns_result(self, full_scenario):
        result = run_simulation(full_scenario)

        assert result is not None
        assert hasattr(result, "monthly_pnl")
        assert hasattr(result, "annual_profit")

    def test_simulation_has_12_months(self, full_scenario):
        result = run_simulation(full_scenario)

        assert len(result.monthly_pnl) == 12

    def test_simulation_with_no_fixed_costs(
        self, session, sample_scenario, sample_product
    ):
        traffic = TrafficAssumption(
            scenario_id=sample_scenario.id,
            daily_customers=100,
            avg_products_per_customer=1.0,
        )
        session.add(traffic)
        for month in Month:
            session.add(
                SeasonalityFactor(
                    scenario_id=sample_scenario.id,
                    month=month,
                    multiplier=1.0,
                )
            )
        session.commit()
        session.refresh(sample_scenario)

        result = run_simulation(sample_scenario)

        assert result is not None
        assert len(result.monthly_pnl) == 12


class TestContributionMargin:
    def test_margin_positive_when_price_above_cost(self, full_scenario):
        result = run_simulation(full_scenario)

        # Espresso: 10 PLN price, 7g of 25 PLN/kg coffee = 0.175 PLN cost
        # Margin should be roughly 9.82 PLN
        assert result.contribution_margin.per_portion > Decimal("9.0")
        assert result.contribution_margin.per_portion < Decimal("10.0")

    def test_margin_percentage_below_100(self, full_scenario):
        """Contribution margin percentage should be less than 100%."""
        result = run_simulation(full_scenario)

        assert result.contribution_margin.ratio < 1.0
        assert result.contribution_margin.ratio > 0.0


class TestMonthlyPnL:
    def test_monthly_pnl_has_month_field(self, full_scenario):
        result = run_simulation(full_scenario)

        for entry in result.monthly_pnl:
            assert hasattr(entry, "month")

    def test_monthly_pnl_has_profit_field(self, full_scenario):
        result = run_simulation(full_scenario)

        for entry in result.monthly_pnl:
            assert hasattr(entry, "profit")

    def test_annual_profit_sums_monthly(self, full_scenario):
        result = run_simulation(full_scenario)

        monthly_sum = sum(entry.profit for entry in result.monthly_pnl)
        assert result.annual_profit == monthly_sum

    def test_seasonality_affects_revenue(
        self, session, sample_scenario, sample_product
    ):

        session.add(
            FixedCost(
                scenario_id=sample_scenario.id,
                name="Rent",
                amount=Decimal("1000.00"),
                category=CostCategory.RENT,
            )
        )
        session.add(
            TrafficAssumption(
                scenario_id=sample_scenario.id,
                daily_customers=100,
                avg_products_per_customer=1.0,
            )
        )

        # Peak in July 2x, baseline other months
        for month in Month:
            multiplier = 2.0 if month == Month.JULY else 1.0
            session.add(
                SeasonalityFactor(
                    scenario_id=sample_scenario.id,
                    month=month,
                    multiplier=multiplier,
                )
            )
        session.commit()
        session.refresh(sample_scenario)

        result = run_simulation(sample_scenario)

        july_entry = next(e for e in result.monthly_pnl if e.month == 7)
        january_entry = next(e for e in result.monthly_pnl if e.month == 1)

        assert july_entry.revenue > january_entry.revenue * Decimal("1.8")
