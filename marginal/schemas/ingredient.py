from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from marginal.constants import (
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
)
from marginal.enums import Unit


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


class IngredientExport(IngredientBase):
    pass
