from decimal import Decimal

from calculations import SimulationResult
from models import FixedCost, Product, Scenario, SeasonalityFactor, TrafficAssumption


def render_simulation(result: SimulationResult) -> None:
    """Print simulation result to terminal."""
    print(f"\n{'=' * 60}")
    print(f"  {result.scenario_name} ({result.currency})")
    print(f"{'=' * 60}\n")

    print(f"Fixed costs: {result.fixed_costs_monthly:.0f} {result.currency}/month")
    print(
        f"Contribution margin: {result.contribution_margin.per_portion:.2f} per portion "
        f"({result.contribution_margin.ratio * 100:.1f}%)"
    )

    print("\nMonthly P&L:")
    print(
        f"{'Month':>6} {'Portions':>10} {'Revenue':>12} {'Variable':>12} {'Profit':>12}"
    )
    print("-" * 60)

    for pnl in result.monthly_pnl:
        marker = "✓" if pnl.profit >= 0 else "✗"
        print(
            f"{pnl.month:>6} {pnl.portions_sold:>10} "
            f"{pnl.revenue:>12.0f} {pnl.variable_costs:>12.0f} "
            f"{pnl.profit:>12.0f} {marker}"
        )

    print("-" * 60)
    print(
        f"{'Annual':>6} {'':>10} "
        f"{result.annual_revenue:>12.0f} {result.annual_variable_costs:>12.0f} "
        f"{result.annual_profit:>12.0f}"
    )


def render_scenarios(scenarios: list[Scenario]) -> None:
    if not scenarios:
        print("\nNo available scenarios.")
        return

    print("\n" + "=" * 65)
    print(" SCENARIOS ")
    print("=" * 65)
    print(f"{'ID / Name':<30} {'Currency':<10} {'Created at':<20}")
    print("-" * 65)

    for scenario in scenarios:
        created_str = str(scenario.created_at).split(".")[0]
        print(f"{scenario.name:<30} {scenario.currency:<10} {created_str:<20}")

    print("=" * 65 + "\n")


def show_scenario(scenario: Scenario) -> None:
    created_str = str(scenario.created_at).split(".")[0]

    print("\n" + "=" * 50)
    print(f" SCENARIO: {scenario.name.upper()} [{scenario.currency}]")
    print("=" * 50)
    print(f" Created: {created_str}")
    print("-" * 50)
    print(" Products:")

    if not scenario.products:
        print("   (No products)")
    else:
        for product in scenario.products:
            print(f"   • {product.name:<30} {product.price:>8.2f} {scenario.currency}")

    print("=" * 50 + "\n")


def show_product(product: Product) -> None:
    """Display detailed product information."""
    print(f"\nProduct: {product.name}")
    print(f"  Price: {product.price}")
    print(f"  Category: {product.category}")
    print(f"  Wastage: {product.wastage_pct * 100:.1f}%")

    if product.recipe_items:
        print("\n  Recipe items:")
        for item in product.recipe_items:
            print(f"    - {item.quantity} {item.unit.value} of {item.ingredient.name}")


def render_products(products: list[Product], currency: str) -> None:
    """Display list of products in a scenario as a table."""
    print("\n" + "=" * 70)
    print(" PRODUCTS ")
    print("=" * 70)
    print(f"{'Name':<35} {'Price':>10} {'Category':<15} {'Wastage':>7}")
    print("-" * 70)

    for product in products:
        print(
            f"{product.name:<35} "
            f"{product.price:>7.2f} {currency:<3} "
            f"{product.category:<15} "
            f"{product.wastage_pct * 100:>5.1f}%"
        )

    print("=" * 70 + "\n")


def render_fixed_costs(costs: list[FixedCost], currency: str) -> None:
    """Display list of fixed costs as a table"""
    print("\n" + "=" * 70)
    print(" FIXED COSTS ")
    print("=" * 70)
    print(f"{'Name':<25} {'Category':<15} {'Amount':>12} {'Notes':<20}")
    print("-" * 70)

    total = Decimal("0")
    for cost in costs:
        notes = cost.notes or ""
        notes_short = notes[:17] + "..." if len(notes) > 20 else notes
        print(
            f"{cost.name:<25} "
            f"{cost.category.value:<15} "
            f"{cost.amount:>8.2f} {currency:<3} "
            f"{notes_short:<20}"
        )
        total += cost.amount

    print("-" * 70)
    print(f"{'Total':<25} {'':<15} {total:>8.2f} {currency:<3}")
    print("=" * 70 + "\n")


def render_traffic_assumption(traffic: TrafficAssumption, scenario_name: str) -> None:
    """Display traffic assumption"""
    print(f"\nTraffic assumption for '{scenario_name}':")
    print(f"  Daily customers:              {traffic.daily_customers}")
    print(f"  Products per customer (avg):  {traffic.avg_products_per_customer}")


def render_seasonality(factors: list[SeasonalityFactor]) -> None:
    """Display seasonality factors as a table."""
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    print("\n" + "=" * 40)
    print(" SEASONALITY FACTORS ")
    print("=" * 40)
    print(f"{'Month':<15} {'Multiplier':>10}")
    print("-" * 40)

    for factor in factors:
        name = month_names.get(factor.month, str(factor.month))
        marker = ""
        if factor.multiplier > 1.5:
            marker = " (high)"
        elif factor.multiplier < 0.5:
            marker = " (low)"
        print(f"{name:<15} {factor.multiplier:>10.2f}{marker}")

    print("=" * 40 + "\n")
