from decimal import Decimal

import typer
from pydantic import ValidationError

from marginal.cli.helpers import _get_product_or_exit, _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import render_products, show_product
from marginal.repository import (
    add_product,
    delete_product,
    get_product_by_name_in_scenario,
    get_products_by_scenario,
    update_product,
)
from marginal.schemas.product import ProductCreate, ProductUpdate

product_app = typer.Typer(help="Product")


@product_app.command("get")
def get_product(scenario_name: str, product_name: str):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        product = _get_product_or_exit(session, scenario, product_name)
        show_product(product)


@product_app.command("list")
def get_products_list(scenario_name: str):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        products = get_products_by_scenario(session, scenario.id)
        if not products:
            typer.echo(
                f"No products in '{scenario_name}'. Add one with 'product create'."
            )
            return

        render_products(products, scenario.currency)


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
        scenario = _get_scenario_or_exit(session, scenario_name)
        existing = get_product_by_name_in_scenario(session, scenario.id, product_name)
        if existing:
            typer.echo(
                f"Product '{product_name}' already exists in '{scenario_name}'",
                err=True,
            )
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
        scenario = _get_scenario_or_exit(session, scenario_name)
        _get_product_or_exit(session, scenario, product_name)

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
        scenario = _get_scenario_or_exit(session, scenario_name)
        _get_product_or_exit(session, scenario, product_name)

        if not force:
            typer.confirm(
                f"Are you sure you want to delete '{product_name}'? this cannot be undone.",
                abort=True,
            )

        res = delete_product(session, scenario.id, product_name)
        if res:
            typer.echo(f"✓ Deleted product '{product_name}'")
        else:
            typer.echo(f"Failed to delete '{product_name}'", err=True)
            raise typer.Exit(code=1)
