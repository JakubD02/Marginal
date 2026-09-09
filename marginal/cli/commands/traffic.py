import typer
from pydantic import ValidationError

from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import render_traffic_assumption
from marginal.repository import (
    get_traffic_assumption_by_scenario,
    set_traffic_assumption,
)
from marginal.schemas.traffic_assumption import TrafficAssumptionCreate

traffic_assumption_app = typer.Typer(help="Traffic assumption")


@traffic_assumption_app.command("set")
def traffic_assumption_set(
    scenario_name: str,
    daily_customers: int | None = typer.Option(
        None, "--customers", "-c", help="Daily customers"
    ),
    avg_product_per_customer: float | None = typer.Option(
        None, "--avg-product", "-ap", help="Average product per customer"
    ),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        if daily_customers is None:
            daily_customers = typer.prompt("Daily customers", type=int)
        if avg_product_per_customer is None:
            avg_product_per_customer = typer.prompt(
                "Average product per customer", type=float
            )

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
def traffic_assumption(scenario_name: str):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        traffic = get_traffic_assumption_by_scenario(session, scenario.id)
        if not traffic:
            typer.echo(
                f"No traffic assumption for '{scenario_name}'. "
                f"Set with 'traffic-assumption set'."
            )
            return

        render_traffic_assumption(traffic, scenario.name)
