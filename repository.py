from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from advisor.schemas import (
    FixedCostCreate,
    IngredientCreate,
    ProductCreate,
    ProductUpdate,
    RecipeItemCreate,
    ScenarioCreate,
    ScenarioUpdate,
    SeasonalityFactorCreate,
    TrafficAssumptionCreate,
)
from models import (
    FixedCost,
    Ingredient,
    Product,
    RecipeItem,
    Scenario,
    SeasonalityFactor,
    TrafficAssumption,
)


# ----- scenario -----
def create_scenario(session: Session, data: ScenarioCreate) -> Scenario:
    scenario = Scenario(**data.model_dump())
    session.add(scenario)
    session.flush()
    return scenario


def get_scenario(session: Session, scenario_id: UUID) -> Scenario | None:
    stmt = select(Scenario).where(Scenario.id == scenario_id)
    return session.execute(stmt).scalar_one_or_none()


def get_scenario_by_name(session: Session, name: str) -> Scenario | None:
    stmt = select(Scenario).where(Scenario.name == name)
    return session.execute(stmt).scalar_one_or_none()


def get_scenario_with_all(session: Session, scenario_id: UUID) -> Scenario | None:
    stmt = (
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .options(
            selectinload(Scenario.fixed_costs),
            selectinload(Scenario.ingredients),
            selectinload(Scenario.products)
            .selectinload(Product.recipe_items)
            .selectinload(RecipeItem.ingredient),
            selectinload(Scenario.traffic_assumption),
            selectinload(Scenario.seasonality_factors),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def list_scenarios(session: Session) -> list[Scenario]:
    stmt = select(Scenario).order_by(Scenario.created_at)
    return list(session.execute(stmt).scalars().all())


def update_scenario(
    session: Session, scenario_id: UUID, scenario_in: ScenarioUpdate
) -> Scenario | None:
    scenario = get_scenario(session=session, scenario_id=scenario_id)
    if not scenario:
        return None

    data = scenario_in.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(scenario, field, value)

    session.flush()
    return scenario


def delete_scenario(session: Session, scenario_id: UUID) -> bool:
    scenario = get_scenario(session, scenario_id)
    if not scenario:
        return False

    session.delete(scenario)
    session.flush()
    return True


# ----- fixed cost -----
def get_fixed_costs_by_scenario(session: Session, scenario_id: UUID) -> list[FixedCost]:
    stmt = select(FixedCost).where(FixedCost.scenario_id == scenario_id)
    return list(session.execute(stmt).scalars().all())


def get_fixed_cost_by_name(
    session: Session, scenario_id: UUID, name: str
) -> Scenario | None:
    stmt = select(FixedCost).where(
        FixedCost.name == name, FixedCost.scenario_id == scenario_id
    )
    return session.execute(stmt).scalar_one_or_none()


def add_fixed_cost(
    session: Session, scenario_id: UUID, data: FixedCostCreate
) -> FixedCost:
    cost = FixedCost(scenario_id=scenario_id, **data.model_dump())
    session.add(cost)
    session.flush()
    return cost


def delete_fixed_cost(
    session: Session, scenario_id: UUID, fixed_cost_name: str
) -> bool:
    fixed_cost = get_fixed_cost_by_name(session, scenario_id, fixed_cost_name)
    if not fixed_cost:
        return False

    session.delete(fixed_cost)
    session.flush()
    return True


# ----- product -----
def add_product(session: Session, scenario_id: UUID, data: ProductCreate) -> Product:
    product = Product(scenario_id=scenario_id, **data.model_dump())
    session.add(product)
    session.flush()
    return product


def get_products_by_scenario(session: Session, scenario_id: UUID) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.scenario_id == scenario_id)
        .options(selectinload(Product.recipe_items).selectinload(RecipeItem.ingredient))
    )
    return list(session.execute(stmt).scalars().all())


def get_product_by_name_in_scenario(
    session: Session, scenario_id: UUID, product_name: str
) -> Product | None:
    stmt = (
        select(Product)
        .where(Product.scenario_id == scenario_id, Product.name == product_name)
        .options(selectinload(Product.recipe_items).selectinload(RecipeItem.ingredient))
    )
    return session.execute(stmt).scalar_one_or_none()


def update_product(
    session: Session, scenario_id: UUID, product_name: str, product_in: ProductUpdate
) -> Product | None:
    product = get_product_by_name_in_scenario(session, scenario_id, product_name)
    if not product:
        return None

    data = product_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(product, field, value)

    session.flush()
    return product


def delete_product(session: Session, scenario_id: UUID, product_name: str) -> bool:
    product = get_product_by_name_in_scenario(session, scenario_id, product_name)
    if not product:
        return False

    session.delete(product)
    session.flush()
    return True


# ----- ingredient -----
def add_ingredient(
    session: Session, scenario_id: UUID, data: IngredientCreate
) -> Ingredient:
    ingredient = Ingredient(scenario_id, **data.model_dump())
    session.add(ingredient)
    session.flush()
    return ingredient


# ----- recipe item -----
def add_recipe_item(
    session: Session, product_id: UUID, data: RecipeItemCreate
) -> RecipeItem:
    recipe_item = RecipeItem(product_id=product_id, **data.model_dump())
    session.add(recipe_item)
    session.flush()
    return recipe_item


# ----- traffic_assumption -----
def set_traffic_assumption(
    session: Session, scenario_id: UUID, data: TrafficAssumptionCreate
) -> TrafficAssumption:
    """Upsert traffic assumption for a scenario"""
    existing = session.execute(
        select(TrafficAssumption).where(TrafficAssumption.scenario_id == scenario_id)
    ).scalar_one_or_none()
    if existing:
        existing.daily_customers = data.daily_customers
        existing.avg_products_per_customer = data.avg_products_per_customer
        session.flush()
        return existing

    traffic_assumption = TrafficAssumption(scenario_id=scenario_id, **data.model_dump())
    session.add(traffic_assumption)
    session.flush()
    return traffic_assumption


def get_traffic_assumption_by_scenario(
    session: Session, scenario_id: UUID
) -> TrafficAssumption:
    stmt = select(TrafficAssumption).where(TrafficAssumption.scenario_id == scenario_id)
    return session.execute(stmt).scalar_one_or_none()


# ----- seasonality factor -----
def set_seasonality_for_month(
    session: Session, scenario_id: UUID, data: SeasonalityFactorCreate
) -> SeasonalityFactor:
    """Upsert seasonality for a specific month"""
    existing = session.execute(
        select(SeasonalityFactor).where(
            SeasonalityFactor.scenario_id == scenario_id,
            SeasonalityFactor.month == data.month,
        )
    ).scalar_one_or_none()

    if existing:
        existing.multiplier = data.multiplier
        session.flush()
        return existing

    factor = SeasonalityFactor(scenario_id=scenario_id, **data.model_dump())
    session.add(factor)
    session.flush()
    return factor


def get_seasonality_by_scenario(
    session: Session, scenario_id: UUID
) -> SeasonalityFactor:
    stmt = (
        select(SeasonalityFactor)
        .where(SeasonalityFactor.scenario_id == scenario_id)
        .order_by(SeasonalityFactor.month)
    )
    return list(session.execute(stmt).scalars().all())


def set_all_seasonality(
    session: Session, scenario_id: UUID, factors: list[SeasonalityFactorCreate]
) -> None:
    """Replace all seasonality factors for scenario"""
    session.execute(
        delete(SeasonalityFactor).where(SeasonalityFactor.scenario_id == scenario_id)
    )
    for factor in factors:
        session.add(SeasonalityFactor(scenario_id=scenario_id, **factor.model_dump()))
    session.flush()
