import typer
from pydantic import ValidationError

from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import render_scenarios, show_scenario
from marginal.repository import (
    create_scenario,
    delete_scenario,
    get_scenario_by_name,
    get_scenario_with_all,
    list_scenarios,
    update_scenario,
)
from marginal.schemas.scenario import ScenarioCreate, ScenarioUpdate

scenario_app = typer.Typer(help="Manage scenarios")


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
def scenario_show(scenario_name: str):
    """Show scenario details"""
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        show_scenario(get_scenario_with_all(session, scenario.id))


@scenario_app.command("delete")
def scenario_delete(
    scenario_name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        if not force:
            typer.confirm(
                f"Are you sure you want to delete '{scenario_name}'? this cannot be undone.",
                abort=True,
            )

        res = delete_scenario(session, scenario.id)
        if res:
            typer.echo(f"✓ Deleted product '{scenario_name}'")
        else:
            typer.echo(f"Failed to delete '{scenario_name}'", err=True)
            raise typer.Exit(code=1)


@scenario_app.command("create")
def scenario_create(
    scenario_name: str,
    currency: str = typer.Option("PLN", "--currency", "-c", help="Currency code"),
    working_days: int = typer.Option(
        22, "--working-days", "-w", help="Working days per month"
    ),
):
    with get_session() as session:
        existing = get_scenario_by_name(session, scenario_name)
        if existing:
            typer.echo(f"Scenario '{scenario_name}' already exists", err=True)
            raise typer.Exit(code=1)
        try:
            data = ScenarioCreate(
                name=scenario_name,
                currency=currency,
                working_days_per_month=working_days,
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        scenario = create_scenario(session, data)
        typer.echo(f"✓ Created scenario '{scenario.name}' ({scenario.currency})")


@scenario_app.command("update")
def scenario_update(
    scenario_name: str,
    new_name: str | None = typer.Option(None, "--name", help="New name"),
    currency: str | None = typer.Option(None, "--currency", "-c"),
    working_days: int | None = typer.Option(None, "--working-days", "-w"),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)

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
