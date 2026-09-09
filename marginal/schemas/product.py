from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from marginal.constants import (
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
)
from marginal.schemas.recipe_item import RecipeItemExport


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


class ProductExport(ProductBase):
    recipe: list[RecipeItemExport] = Field(default_factory=list)
