from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from constants import (
    CURRENCY_CODE_LENGTH,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    NOTES_MAX_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
)
from enums import CostCategory, Month, Unit


# ----- scenario -----
class ScenarioBase(BaseModel):
    name: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    currency: str = Field(
        min_length=CURRENCY_CODE_LENGTH, max_length=CURRENCY_CODE_LENGTH
    )
    working_days_per_month: int = Field(default=22, ge=1, le=31)


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    currency: str | None = Field(
        default=None, min_length=CURRENCY_CODE_LENGTH, max_length=CURRENCY_CODE_LENGTH
    )
    working_days_per_month: int | None = Field(default=None, ge=1, le=31)


class ScenarioRead(ScenarioBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- fixed cost -----
class FixedCostBase(BaseModel):
    name: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    amount: Decimal = Field(
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    category: CostCategory = CostCategory.OTHER
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class FixedCostCreate(FixedCostBase):
    pass


class FixedCostUpdate(BaseModel):
    scenario_id: UUID | None
    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    category: CostCategory | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class FixedCostRead(FixedCostBase):
    id: UUID
    scenario_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- product -----
class ProductBase(BaseModel):
    name: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    price: Decimal = Field(
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    category: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    wastage_pct: float = Field(default=0.0, ge=0.0, le=1.0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    category: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    wastage_pct: float | None = Field(default=None, ge=0.0, le=1.0)


class ProductRead(ProductBase):
    id: UUID
    scenario_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ----- ingredient -----
class IngredientBase(BaseModel):
    name: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    purchase_price: Decimal = Field(
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    purchase_unit: Unit = Field(
        default=Unit.KG,
    )
    unit_size: float = Field(default=1.0, gt=0)


class IngredientCreate(IngredientBase):
    pass


class IngredientUpdate(BaseModel):
    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    purchase_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
    )
    purchase_unit: Unit | None = Field(
        default=None,
    )
    unit_size: float | None = Field(default=None, gt=0)


class IngredientRead(IngredientBase):
    id: UUID
    scenario_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ----- recipe item -----
class RecipeItemBase(BaseModel):
    quantity: float = Field(gt=0)
    unit: Unit = Field(default=Unit.KG)


class RecipeItemCreate(RecipeItemBase):
    ingredient_id: UUID


class RecipeItemUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    unit: Unit | None = Field(default=Unit.KG)


class RecipeItemRead(RecipeItemBase):
    product_id: UUID
    ingredient_id: UUID
    ingredient: IngredientRead  # to have not only ID

    model_config = ConfigDict(from_attributes=True)


# ----- traffic_assumption -----
class TrafficAssumptionBase(BaseModel):
    daily_customers: int = Field(ge=0)
    avg_products_per_customer: float = Field(ge=0)


class TrafficAssumptionCreate(TrafficAssumptionBase):
    pass


class TrafficAssumptionUpdate(BaseModel):
    daily_customers: int | None = Field(default=None, ge=0)
    avg_products_per_customer: float | None = Field(default=None, ge=0)


class TrafficAssumptionRead(TrafficAssumptionBase):
    scenario_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ----- seasonality factor -----
class SeasonalityFactorBase(BaseModel):
    month: Month
    multiplier: float = Field(gt=0)


class SeasonalityFactorCreate(SeasonalityFactorBase):
    pass


class SeasonalityFactorUpdate(BaseModel):
    multiplier: float | None = Field(default=None, gt=0)


class SeasonalityFactorRead(SeasonalityFactorBase):
    scenario_id: UUID

    model_config = ConfigDict(from_attributes=True)
