import typer
from pydantic import ValidationError

from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import render_seasonality
from marginal.repository import get_seasonality_by_scenario, set_seasonality_for_month
from marginal.schemas.seasonality_factor import SeasonalityFactorCreate

seasonality_app = typer.Typer(help="Seasonality factor")


@seasonality_app.command("set")
def seasonality_factor_set(
    scenario_name: str,
    month: int | None = typer.Option(None, "--month", "-m", help="Month (1-12)"),
    multiplier: float | None = typer.Option(
        None, "--multiplier", "-x", help="Seasonality multiplier"
    ),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
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
        scenario = _get_scenario_or_exit(session, scenario_name)
        factors = get_seasonality_by_scenario(session, scenario.id)
        if not factors:
            typer.echo(
                f"No seasonality factors for '{scenario_name}'. "
                f"Set with 'seasonality set'."
            )
            return

        render_seasonality(factors)
