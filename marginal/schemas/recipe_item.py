from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from marginal.enums import Unit
from marginal.schemas.ingredient import IngredientRead


class RecipeItemBase(BaseModel):
    quantity: float = Field(gt=0)
    unit: Unit = Field(default=Unit.KG)


class RecipeItemCreate(RecipeItemBase):
    ingredient_id: UUID


class RecipeItemUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    unit: Unit | None = Field(default=None, gt=0)


class RecipeItemRead(RecipeItemBase):
    product_id: UUID
    ingredient_id: UUID
    ingredient: IngredientRead  # to have not only ID

    model_config = ConfigDict(from_attributes=True)


class RecipeItemExport(RecipeItemBase):
    ingredient: str

    @field_validator("ingredient", mode="before")
    @classmethod
    def extract_ingredient_name(cls, value):
        if hasattr(value, "name"):
            return value.name
        return value
