from calculations import SimulationResult
from models import Product, Scenario


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
