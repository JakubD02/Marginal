from calculations import (
    compute_monthly_pnl,
    run_simulation,
)
from database import get_session
from repository import get_products_by_scenario, get_scenario_by_name

with get_session() as session:
    scenario = get_scenario_by_name(session, "Ice cream parlor 59")
    products = get_products_by_scenario(session, scenario.id)
    if not scenario:
        print("Scenario not found")
        exit()

    result = run_simulation(scenario)
    
    print(f"\n{'='*60}")
    print(f"  {result.scenario_name} ({result.currency})")
    print(f"{'='*60}\n")
    
    print(f"Fixed costs: {result.fixed_costs_monthly:.0f} {result.currency}/month")
    print(f"Contribution margin: {result.contribution_margin.per_portion:.2f} per portion "
          f"({result.contribution_margin.ratio * 100:.1f}%)")
    
    print(f"\nMonthly P&L:")
    print(f"{'Month':>6} {'Portions':>10} {'Revenue':>12} {'Variable':>12} {'Profit':>12}")
    print("-" * 60)

    for pnl in result.monthly_pnl:
        marker = "✓" if pnl.profit >= 0 else "✗"
        print(f"{pnl.month:>6} {pnl.portions_sold:>10} "
              f"{pnl.revenue:>12.0f} {pnl.variable_costs:>12.0f} "
              f"{pnl.profit:>12.0f} {marker}")
    
    print("-" * 60)
    print(f"{'Annual':>6} {'':>10} "
          f"{result.annual_revenue:>12.0f} {result.annual_variable_costs:>12.0f} "
          f"{result.annual_profit:>12.0f}")