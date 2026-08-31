from decimal import Decimal

import typer
from pydantic import ValidationError

from advisor.schemas import (
    FixedCostCreate,
    ProductCreate,
    ProductUpdate,
    ScenarioCreate,
    ScenarioUpdate,
    SeasonalityFactorCreate,
    TrafficAssumptionCreate,
)
from calculations import run_simulation
from database import get_session
from enums import CostCategory
from presenters import (
    render_fixed_costs,
    render_products,
    render_scenarios,
    render_seasonality,
    render_simulation,
    render_traffic_assumption,
    show_product,
    show_scenario,
)
from repository import (
    add_fixed_cost,
    add_product,
    create_scenario,
    delete_fixed_cost,
    delete_product,
    delete_scenario,
    get_fixed_cost_by_name,
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

app = typer.Typer(help="Marginal - business profitability simulator")

scenario_app = typer.Typer(help="Manage scenarios")
app.add_typer(scenario_app, name="scenario")

product_app = typer.Typer(help="Product")
app.add_typer(product_app, name="product")

fixed_cost_app = typer.Typer(help="Fixed cost")
app.add_typer(fixed_cost_app, name="fixed-cost")

traffic_assumption_app = typer.Typer(help="Traffic assumption")
app.add_typer(traffic_assumption_app, name="traffic-assumption")

seasonality_app = typer.Typer(help="Seasonality factor")
app.add_typer(seasonality_app, name="seasonality")


@app.command()
def simulate(scenario_name: str):
    """Run full simulation for scenario"""
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        result = run_simulation(scenario)
        render_simulation(result)


# ----- scenario -----


@scenario_app.command("list")
def scenario_list():
    """List all scenarios"""
    with get_session() as session:
        scenarios = list_scenarios(session)
        if not scenarios:
            typer.echo("No scenarios found. Create one with 'marginal scenario create'")
            return

        render_scenarios(scenarios)


@scenario_app.command("show")
def scenario_show(name: str):
    """Show scenario details"""
    with get_session() as session:
        scenario = get_scenario_by_name(session, name)
        if not scenario:
            typer.echo(f"Scenario '{name}' not found", err=True)
            raise typer.Exit(code=1)

        scenario = get_scenario_with_all(session, scenario.id)
        show_scenario(scenario)


@scenario_app.command("delete")
def scenario_delete(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, name)
        if not scenario:
            typer.echo(f"Scenario '{name}' not found", err=True)
            raise typer.Exit(code=1)

        if not force:
            typer.confirm(
                f"Are you sure you want to delete '{name}'? this cannot be undone.",
                abort=True,
            )

        res = delete_scenario(session, scenario.id)
        if res:
            typer.echo(f"Successfully removed '{name}'")
        else:
            typer.echo(f"Failed to delete '{name}'", err=True)
            raise typer.Exit(code=1)


@scenario_app.command("create")
def scenario_create(
    name: str,
    currency: str = typer.Option("PLN", "--currency", "-c", help="Currency code"),
    working_days: int = typer.Option(
        22, "--working-days", "-w", help="Working days per month"
    ),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, name)
        if scenario:
            typer.echo(f"Scenario '{name}' already exists", err=True)
            raise typer.Exit(code=1)

        try:
            data = ScenarioCreate(
                name=name, currency=currency, working_days_per_month=working_days
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        scenario = create_scenario(session, data)
        typer.echo(f"✓ Created scenario '{scenario.name}' ({scenario.currency})")


@scenario_app.command("update")
def scenario_update(
    name: str,
    new_name: str | None = typer.Option(None, "--name", help="New name"),
    currency: str | None = typer.Option(None, "--currency", "-c"),
    working_days: int | None = typer.Option(None, "--working-days", "-w"),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, name)
        if not scenario:
            typer.echo(f"Scenario '{name}' not found", err=True)
            raise typer.Exit(code=1)

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name
        if currency is not None:
            update_data["currency"] = currency
        if working_days is not None:
            update_data["working_days_per_month"] = working_days

        if not update_data:
            typer.echo(
                "No fields to update. Use --name, --currency, or --working-days.",
                err=True,
            )
            raise typer.Exit(code=1)

        try:
            data = ScenarioUpdate(**update_data)
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        updated = update_scenario(session, scenario.id, data)
        typer.echo(f"✓ Updated scenario '{updated.name}'")


# ----- product -----
@product_app.command("get")
def get_product(scenario_name: str, product_name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1) from None

        product = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if not product:
            typer.echo(f"Product '{product_name}' not found", err=True)
            raise typer.Exit(code=1) from None

        show_product(product)


@product_app.command("list")
def get_products_list(scenario_name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        products = get_products_by_scenario(session, scenario.id)
        if not products:
            typer.echo(
                f"No products in '{scenario_name}'. Add one with 'product create'."
            )
            return

        render_products(products)


@product_app.command("create")
def product_add(
    scenario_name: str,
    product_name: str,
    price: str | None = typer.Option(None, "--price", "-p", help="Product price"),
    category: str | None = typer.Option(
        None, "--category", "-c", help="Product category"
    ),
    wastage_pct: float = typer.Option(
        0.05, "--wastage", "-w", help="Wastage percentage (0.0-1.0)"
    ),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' does not exist!", err=True)
            raise typer.Exit(code=1)

        product = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if product:
            typer.echo(f"Product '{product_name}' already exists", err=True)
            raise typer.Exit(code=1)

        if price is None:
            price = typer.prompt("Product price", type=Decimal)
        if category is None:
            category = typer.prompt("Product category", default="food")

        try:
            price = Decimal(price)
        except ValueError:
            typer.echo("Invalid price", err=True)
            raise typer.Exit(code=1) from None

        try:
            data = ProductCreate(
                name=product_name,
                price=price,
                category=category,
                wastage_pct=wastage_pct,
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        product = add_product(session, scenario.id, data)
        typer.echo(
            f"✓ Added product '{product.name}' ({product.price} {scenario.currency})"
        )


@product_app.command("update")
def product_update(
    scenario_name: str,
    product_name: str,
    new_name: str | None = typer.Option(None, "--name", "-n", help="New name"),
    price: str | None = typer.Option(None, "--price", "-p", help="Product price"),
    category: str | None = typer.Option(
        None, "--category", "-c", help="Product category"
    ),
    wastage_pct: float | None = typer.Option(
        None, "--wastage", "-w", help="Wastage percentage (0.0-1.0)"
    ),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' does not exists!", err=True)
            raise typer.Exit(code=1)

        product = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if not product:
            typer.echo(
                f"Product '{product_name}' not found in '{scenario_name}'", err=True
            )
            raise typer.Exit(code=1)

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name
        if price is not None:
            try:
                price = Decimal(price)
            except ValueError:
                typer.echo("Invalid price", err=True)
                raise typer.Exit(code=1) from None
            update_data["price"] = price
        if category is not None:
            update_data["category"] = category
        if wastage_pct is not None:
            update_data["wastage_pct"] = wastage_pct

        if not update_data:
            typer.echo(
                "No fields to update. Use --name, --price, --category, or --wastage.",
                err=True,
            )
            raise typer.Exit(code=1)

        try:
            data = ProductUpdate(**update_data)
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        updated = update_product(session, scenario.id, product_name, data)
        typer.echo(f"✓ Updated product '{updated.name}'")


@product_app.command("delete")
def product_delete(
    scenario_name: str,
    product_name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)
        product = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if not product:
            typer.echo(
                f"Product '{product_name}' not found in '{scenario_name}'", err=True
            )
            raise typer.Exit(code=1)

        if not force:
            typer.confirm(
                f"Are you sure you want to delete '{product_name}'? this cannot be undone.",
                abort=True,
            )

        res = delete_product(session, scenario.id, product_name)
        if res:
            typer.echo(f"Successfully removed '{product_name}'")
        else:
            typer.echo(f"Failed to delete '{product_name}'", err=True)
            raise typer.Exit(code=1)


# ----- fixed_cost -----
@fixed_cost_app.command("list")
def fixed_cost_list(
    scenario_name: str,
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        costs = get_fixed_costs_by_scenario(session, scenario.id)
        if not costs:
            typer.echo(
                f"No fixed costs in '{scenario_name}'. Add one with 'fixed-cost add'."
            )
            return

        render_fixed_costs(costs, scenario.currency)


@fixed_cost_app.command("add")
def fixed_cost_add(
    scenario_name: str,
    cost_name: str = typer.Argument(None, help="Cost name"),
    amount: str = typer.Argument(None, help="Amount"),
    category: CostCategory = typer.Option(
        CostCategory.OTHER, "--category", "-c", help="Cost category"
    ),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notes"),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)
        fixed_cost = get_fixed_cost_by_name(session, scenario.id, cost_name)
        if fixed_cost:
            typer.echo(f"Fixed cost '{fixed_cost.name}' already exists", err=True)
            raise typer.Exit(code=1)

        if cost_name is None:
            cost_name = typer.prompt("Cost name")
        if amount is None:
            amount = typer.prompt("Amount")

        try:
            amount = Decimal(amount)
        except ValueError:
            typer.echo("Invalid amount", err=True)
            raise typer.Exit(code=1) from None

        try:
            data = FixedCostCreate(
                name=cost_name,
                amount=amount,
                category=category,
                notes=notes,
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        fixed_cost = add_fixed_cost(session, scenario.id, data)
        typer.echo(f"✓ Created fixed cost '{fixed_cost.name}'")


@fixed_cost_app.command("delete")
def fixed_cost_delete(
    scenario_name: str,
    fixed_cost_name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)
        fixed_cost = get_fixed_cost_by_name(session, scenario.id, fixed_cost_name)
        if not fixed_cost:
            typer.echo(f"Fixed cost '{fixed_cost_name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(
                f"Are you sure you want to delete '{fixed_cost_name}'? this cannot be undone.",
                abort=True,
            )

        res = delete_fixed_cost(session, scenario.id, fixed_cost_name)
        if res:
            typer.echo(f"Successfully removed '{fixed_cost_name}'")
        else:
            typer.echo(f"Failed to delete '{fixed_cost_name}'", err=True)
            raise typer.Exit(code=1)


# ----- traffic assumption -----
@traffic_assumption_app.command("set")
def traffic_assumption_set(
    scenario_name: str,
    daily_customers: int = typer.Option(
        None, "--customers", "-c", help="Daily customers"
    ),
    avg_product_per_customer: float = typer.Option(
        None, "--avg-product", "-ap", help="Average product per customer"
    ),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        if daily_customers is None:
            daily_customers = typer.prompt("Daily customers")
        if avg_product_per_customer is None:
            avg_product_per_customer = typer.prompt("Average product per customer")

        try:
            data = TrafficAssumptionCreate(
                daily_customers=daily_customers,
                avg_products_per_customer=avg_product_per_customer,
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        traffic = set_traffic_assumption(session, scenario.id, data)
        typer.echo(
            f"✓ Traffic set for '{scenario.name}': "
            f"{traffic.daily_customers} customers/day, "
            f"{traffic.avg_products_per_customer} products/customer"
        )


@traffic_assumption_app.command("get")
def traffic_assumption_factor(scenario_name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        traffic = get_traffic_assumption_by_scenario(session, scenario.id)
        if not traffic:
            typer.echo(
                f"No traffic assumption for '{scenario_name}'. "
                f"Set with 'traffic-assumption set'."
            )
            return

        render_traffic_assumption(traffic, scenario.name)


# ----- seasonality factor -----


@seasonality_app.command("set")
def seasonality_factor_set(
    scenario_name: str,
    month: int | None = typer.Option(None, "--month", "-m", help="Month (1-12)"),
    multiplier: float | None = typer.Option(
        None, "--multiplier", "-x", help="Seasonality multiplier"
    ),
):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        if month is None:
            month = typer.prompt("Month (1-12)", type=int)
        if multiplier is None:
            multiplier = typer.prompt("Multiplier", type=float)

        try:
            data = SeasonalityFactorCreate(month=month, multiplier=multiplier)
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        factor = set_seasonality_for_month(session, scenario.id, data)
        typer.echo(
            f"✓ Seasonality set for '{scenario.name}': "
            f"month {factor.month} = {factor.multiplier}x"
        )


@seasonality_app.command("list")
def seasonality_list(scenario_name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        factors = get_seasonality_by_scenario(session, scenario.id)
        if not factors:
            typer.echo(
                f"No seasonality factors for '{scenario_name}'. "
                f"Set with 'seasonality set'."
            )
            return

        render_seasonality(factors)


if __name__ == "__main__":
    app()
