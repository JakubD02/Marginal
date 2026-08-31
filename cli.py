from decimal import Decimal

import typer
from pydantic import ValidationError

from advisor.schemas import (
    FixedCostCreate,
    ProductCreate,
    ProductUpdate,
    ScenarioCreate,
    ScenarioUpdate,
)
from calculations import run_simulation
from database import get_session
from enums import CostCategory
from presenters import (
    render_fixed_costs,
    render_products,
    render_scenarios,
    render_simulation,
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
    list_scenarios,
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


# ----- seasonality factor -----


if __name__ == "__main__":
    app()
