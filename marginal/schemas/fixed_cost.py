from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from marginal.constants import (
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    NOTES_MAX_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
)
from marginal.enums import CostCategory


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
    scenario_id: UUID | None = None
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


class FixedCostExport(FixedCostBase):
    model_config = ConfigDict(from_attributes=True)
