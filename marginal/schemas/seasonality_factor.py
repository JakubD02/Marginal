from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from marginal.enums import Month


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


class SeasonalityFactorExport(SeasonalityFactorBase):
    pass
