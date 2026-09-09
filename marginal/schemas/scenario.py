from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from marginal.constants import CURRENCY_CODE_LENGTH, NAME_MAX_LENGTH, NAME_MIN_LENGTH
from marginal.schemas.fixed_cost import FixedCostExport
from marginal.schemas.ingredient import IngredientExport
from marginal.schemas.product import ProductExport
from marginal.schemas.seasonality_factor import SeasonalityFactorExport
from marginal.schemas.traffic_assumption import TrafficAssumptionExport


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


class ScenarioExport(ScenarioBase):
    fixed_costs: list[FixedCostExport] = Field(default_factory=list)
    products: list[ProductExport] = Field(default_factory=list)
    ingredients: list[IngredientExport] = Field(default_factory=list)

    traffic: TrafficAssumptionExport | None = None
    seasonality: list[SeasonalityFactorExport] = Field(default_factory=list)
