from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class TrafficAssumptionExport(TrafficAssumptionBase):
    model_config = ConfigDict(from_attributes=True)
