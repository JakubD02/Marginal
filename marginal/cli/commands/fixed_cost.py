from decimal import Decimal

import typer
from pydantic import ValidationError

from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.enums import CostCategory
from marginal.presenters import render_fixed_costs
from marginal.repository import (
    add_fixed_cost,
    delete_fixed_cost,
    get_fixed_cost_by_name,
    get_fixed_costs_by_scenario,
)
from marginal.schemas.fixed_cost import FixedCostCreate

fixed_cost_app = typer.Typer(help="Fixed cost")


@fixed_cost_app.command("list")
def fixed_cost_list(
    scenario_name: str,
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
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
    amount: str | None = typer.Argument(None, help="Amount"),
    category: CostCategory = typer.Option(
        CostCategory.OTHER, "--category", "-c", help="Cost category"
    ),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notes"),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)

        if cost_name is None:
            cost_name = typer.prompt("Cost name")
        if amount is None:
            amount = typer.prompt("Amount")

        fixed_cost = get_fixed_cost_by_name(session, scenario.id, cost_name)
        if fixed_cost:
            typer.echo(f"Fixed cost '{fixed_cost.name}' already exists", err=True)
            raise typer.Exit(code=1)

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
        typer.echo(
            f"✓ Added fixed cost '{fixed_cost.name}' ({fixed_cost.amount} {scenario.currency})"
        )


@fixed_cost_app.command("delete")
def fixed_cost_delete(
    scenario_name: str,
    fixed_cost_name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
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
            typer.echo(f"✓ Deleted fixed cost '{fixed_cost_name}'")
        else:
            typer.echo(f"Failed to delete '{fixed_cost_name}'", err=True)
            raise typer.Exit(code=1)
