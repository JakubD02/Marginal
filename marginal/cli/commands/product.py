from decimal import Decimal

import typer
from pydantic import ValidationError

from marginal.calculations import get_sales_share_per_scenario
from marginal.cli.helpers import _get_product_or_exit, _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import (
    render_expected_sales_shares,
    render_products,
    show_product,
)
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
    sales_share: float = typer.Option(
        0.0, "--sales-share", "-s", help="Expected sales share (0.0-1.0)"
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
                expected_sales_share=sales_share,
            )
        except ValidationError as e:
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1) from None

        product = add_product(session, scenario.id, data)
        typer.echo(
            f"✓ Added product '{product.name}' ({product.price} {scenario.currency})"
        )
        sales_shares_val = get_sales_share_per_scenario(scenario.products)
        if sales_shares_val != Decimal("1.0"):
            print(
                f"Warning: total sales share is now {sales_shares_val}% (target: 100%)"
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


@product_app.command("set-sales-share")
def set_sales_shaes_transfer(
    scenario_name: str,
    product_name: str,
    value: float,
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        product = _get_product_or_exit(session, scenario, product_name)

        if value < 1 or value > 100:
            typer.echo("Percentage value should be between 1 and 100!")
            raise typer.Exit(code=1)

        product.expected_sales_share = value / 100
        session.commit()
        typer.echo(f"✓ Set {value}% share to '{product.name}'")
        render_expected_sales_shares(scenario.products, scenario.currency)


@product_app.command("transfer-sales-share")
def change_sales_shares_transfer(
    scenario_name: str = typer.Argument(help="Name of the scenario"),
    from_product_name: str = typer.Argument(help="Product to take share from"),
    to_product_name: str = typer.Argument(help="Product to give share to"),
    value: float = typer.Argument(
        help="Percentage value to transfer (e.g. 10 for 10%)"
    ),
):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        p1 = _get_product_or_exit(session, scenario, from_product_name)
        p2 = _get_product_or_exit(session, scenario, to_product_name)

        if value < 1 or value > 100:
            typer.echo("Percentage value should be between 1 and 100!")
            raise typer.Exit(code=1)

        fraction = value / 100.0

        if p1.expected_sales_share < fraction:
            typer.echo(
                f"Error: Product '{p1.name}' has only {p1.expected_sales_share * 100:.1f}% share, cannot subtract {value}%.",
                err=True,
            )
            raise typer.Exit(code=1)

        p1.expected_sales_share -= fraction
        p2.expected_sales_share += fraction

        session.commit()
        typer.echo(f"✓ Transferred {value}% share from '{p1.name}' to '{p2.name}'")

        render_expected_sales_shares(scenario.products, scenario.currency)
