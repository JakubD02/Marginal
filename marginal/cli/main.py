import typer

from marginal.cli.commands import (
    fixed_cost_app,
    product_app,
    scenario_app,
    seasonality_app,
    traffic_assumption_app,
)
from marginal.cli.simulate import simulate

app = typer.Typer(help="Marginal - business profitability simulator")

app.add_typer(scenario_app, name="scenario")
app.add_typer(product_app, name="product")
app.add_typer(fixed_cost_app, name="fixed-cost")
app.add_typer(traffic_assumption_app, name="traffic-assumption")
app.add_typer(seasonality_app, name="seasonality")

app.command()(simulate)
