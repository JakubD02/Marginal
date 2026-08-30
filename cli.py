from decimal import Decimal

import typer
from pydantic import ValidationError

from advisor.schemas import ScenarioCreate, ScenarioUpdate
from calculations import run_simulation
from database import get_session
from presenters import render_scenarios, render_simulation, show_product, show_scenario
from repository import (
    create_scenario,
    delete_scenario,
    get_product_by_name_in_scenario,
    get_scenario_by_name,
    get_scenario_with_all,
    list_scenarios,
    update_scenario,
)

app = typer.Typer(help="Marginal - business profitability simulator")

scenario_app = typer.Typer(help="Manage scenarios")
app.add_typer(scenario_app, name="scenario")

product_app = typer.Typer(help="Product")
app.add_typer(product_app, name="product")


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
def scenario_delete(name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, name)
        if not scenario:
            typer.echo(f"Scenario '{name}' not found", err=True)
            raise typer.Exit(code=1)

        typer.confirm(
            f"Are you sure you want to delete '{name}'? this cannot be undone.",
            abort=True,
        )

        res = delete_scenario(session, scenario.id)
        if res:
            typer.echo(f"Successfully removed '{name}'")


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

        if currency is None:
            currency = typer.prompt("Currency", default="PLN")
        if working_days is None:
            working_days = typer.prompt("Working days per month", default=22, type=int)

        try:
            data = ScenarioCreate(
                name=name, currency=currency, working_days_per_month=working_days
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1)

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
            raise typer.Exit(code=1)

        updated = update_scenario(session, scenario.id, data)
        typer.echo(f"✓ Updated scenario '{updated.name}'")


# ----- product -----
@product_app.command("get")
def get_product(scenario_name: str, product_name: str):
    with get_session() as session:
        scenario = get_scenario_by_name(session, scenario_name)
        if not scenario:
            typer.echo(f"Scenario '{scenario_name}' not found", err=True)
            raise typer.Exit(code=1)

        product = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if not product:
            typer.echo(f"Product '{product_name}' not found", err=True)
            raise typer.Exit(code=1)

        show_product(product)


# @product_app.command("create")
# def product_create(
#     scenario_name: str,
#     product_name: str,
#     price: Decimal,
#     category: str,
#     wastage_pct: float,
# ):
#     pass


# ----- fixed_cost -----


# ----- traffic assumption -----


# ----- seasonality factor -----


if __name__ == "__main__":
    app()
