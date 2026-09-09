import typer
from sqlalchemy.orm import Session

from marginal.models import Product, Scenario
from marginal.repository import get_product_by_name_in_scenario, get_scenario_by_name


def _get_scenario_or_exit(session: Session, name: str) -> Scenario:
    """Get scenario by name or exit with error message"""
    scenario = get_scenario_by_name(session, name)
    if not scenario:
        typer.echo(f"Scenario '{name}' not found", err=True)
        raise typer.Exit(code=1)
    return scenario


def _get_product_or_exit(
    session: Session, scenario: Scenario, product_name: str
) -> Product:
    """Get product by name or exit with error message"""
    product = get_product_by_name_in_scenario(session, scenario.id, product_name)
    if not product:
        typer.echo(f"Product '{product_name}' not found", err=True)
        raise typer.Exit(code=1)
    return product
