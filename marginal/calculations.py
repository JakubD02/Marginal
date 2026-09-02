import math
from dataclasses import dataclass
from decimal import Decimal

from marginal.units import convert


@dataclass
class ContributionMargin:
    per_portion: Decimal
    ratio: float


@dataclass
class MonthlyPnL:
    month: int
    portions_sold: int
    revenue: Decimal
    variable_costs: Decimal
    fixed_costs: Decimal
    profit: Decimal


@dataclass
class BreakEvenPoint:
    portions_monthly: int
    portions_daily: int
    customers_daily: int | None


@dataclass
class SimulationResult:
    scenario_name: str
    currency: str
    fixed_costs_monthly: Decimal
    contribution_margin: ContributionMargin
    monthly_pnl: list[MonthlyPnL]
    annual_revenue: Decimal
    annual_variable_costs: Decimal
    annual_profit: Decimal


def compute_unit_cost(product) -> Decimal:
    """alculate cost of manufacturing one portion"""
    total = Decimal(0)

    for item in product.recipe_items:
        recipe_item_unit = item.quantity
        ingredient_unit = item.ingredient.purchase_unit
        ingredient_size = item.ingredient.unit_size
        ingredient_price = item.ingredient.purchase_price

        factor = convert(ingredient_size, ingredient_unit, item.unit) / recipe_item_unit
        factor_decimal = Decimal(str(factor))

        per_portion = ingredient_price / factor_decimal
        total += per_portion

    wastage_factor = Decimal(1) + Decimal(str(product.wastage_pct))
    total *= wastage_factor

    return total


def compute_product_margin(product) -> float:
    """Calculate profit margin for a single product"""
    item_cost = compute_unit_cost(product)
    return float((product.price - item_cost) / product.price)


def compute_product_contribution_margin(product) -> ContributionMargin:
    """Calculate contribution margin for a single product"""
    per_portion = product.price - compute_unit_cost(product)
    ratio = compute_product_margin(product)
    return ContributionMargin(per_portion=per_portion, ratio=ratio)


def compute_scenario_contribution_margin(scenario) -> ContributionMargin:
    """Average contribution margin across all products in scenario"""
    products = scenario.products
    if not products:
        raise ValueError("Scenario has no products!")

    margins = [compute_product_contribution_margin(p) for p in products]

    avg_per_portion = sum(m.per_portion for m in margins) / len(margins)
    avg_ratio = sum(m.ratio for m in margins) / len(margins)

    return ContributionMargin(per_portion=avg_per_portion, ratio=avg_ratio)


def get_fixed_costs(scenario) -> Decimal:
    """To get all fixed costs in choosen scenario"""
    total = Decimal(0)
    for cost in scenario.fixed_costs:
        total += cost.amount
    return total


def compute_bep(scenario) -> int:
    """To get compute bep (by month), at beginning margin is calculated by average of items"""
    fixed_costs = get_fixed_costs(scenario)
    cm = compute_scenario_contribution_margin(scenario)

    portions_monthly = math.ceil(fixed_costs / cm.per_portion)
    portions_daily = math.ceil(portions_monthly / scenario.working_days_per_month)

    customers_daily = None
    if scenario.traffic_assumption:
        ppc = scenario.traffic_assumption.avg_products_per_customer
        customers_daily = math.ceil(portions_daily / ppc)

    return BreakEvenPoint(portions_monthly, portions_daily, customers_daily)


def _get_seasonality_for_month(scenario, month: int) -> float:
    """Get seasonality multiplier for month, or 1.0 if not defined"""
    for factor in scenario.seasonality_factors:
        if factor.month == month:
            return factor.multiplier
    return 1.0


def compute_monthly_pnl(scenario, month: int) -> MonthlyPnL:
    """Compute profit and loss for a specific month, accounting for seasonality"""
    if not scenario.products:
        raise ValueError("Scenario has no products")
    if not scenario.traffic_assumption:
        raise ValueError("Scenario has no traffic assumption")

    fixed_costs = get_fixed_costs(scenario)
    daily_portion_base = (
        scenario.traffic_assumption.daily_customers
        * scenario.traffic_assumption.avg_products_per_customer
    )
    monthly_portion_base = scenario.working_days_per_month * daily_portion_base

    seasonality_multiplier = _get_seasonality_for_month(scenario, month)
    monthly_portions = int(monthly_portion_base * seasonality_multiplier)
    monthly_portions_dec = Decimal(str(monthly_portions))

    avg_price = sum(p.price for p in scenario.products) / len(scenario.products)
    avg_cost = sum(compute_unit_cost(p) for p in scenario.products) / len(
        scenario.products
    )

    revenue = monthly_portions_dec * avg_price
    variable_costs = monthly_portions_dec * avg_cost

    profit = revenue - fixed_costs - variable_costs

    return MonthlyPnL(
        month=month,
        portions_sold=monthly_portions,
        revenue=revenue,
        variable_costs=variable_costs,
        fixed_costs=fixed_costs,
        profit=profit,
    )


def run_simulation(scenario) -> SimulationResult:
    if not scenario.products:
        raise ValueError("Scenario has no products")
    if not scenario.fixed_costs:
        raise ValueError("Scenario has no fixed costs")

    annual_revenue = annual_variable_costs = annual_profit = Decimal(0)
    monthly_pnl = []
    for m in range(1, 13):
        res = compute_monthly_pnl(scenario=scenario, month=m)
        monthly_pnl.append(res)
        annual_revenue += res.revenue
        annual_variable_costs += res.variable_costs
        annual_profit += res.profit

    return SimulationResult(
        scenario_name=scenario.name,
        currency=scenario.currency,
        fixed_costs_monthly=get_fixed_costs(scenario),
        contribution_margin=compute_scenario_contribution_margin(scenario),
        monthly_pnl=monthly_pnl,
        annual_revenue=annual_revenue,
        annual_variable_costs=annual_variable_costs,
        annual_profit=annual_profit,
    )
