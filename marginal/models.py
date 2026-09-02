from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from marginal.constants import (
    CURRENCY_CODE_LENGTH,
    NAME_MAX_LENGTH,
    NOTES_MAX_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
)
from marginal.enums import CostCategory, Unit


class Base(DeclarativeBase):
    pass


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(CURRENCY_CODE_LENGTH), nullable=False, index=True
    )
    working_days_per_month: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=22
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    fixed_costs: Mapped[list["FixedCost"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    traffic_assumption: Mapped["TrafficAssumption | None"] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    seasonality_factors: Mapped[list["SeasonalityFactor"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "working_days_per_month BETWEEN 1 AND 31",
            name="working_days_range",
        ),
    )


class FixedCost(Base):
    __tablename__ = "fixed_costs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES), nullable=False
    )
    category: Mapped[CostCategory] = mapped_column(
        SqlEnum(CostCategory, native_enum=False),
        default=CostCategory.OTHER,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(NOTES_MAX_LENGTH), nullable=True)

    scenario: Mapped["Scenario"] = relationship(back_populates="fixed_costs")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    price: Mapped[Decimal] = mapped_column(
        Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES), nullable=False
    )
    category: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    wastage_pct: Mapped[float] = mapped_column(nullable=False, default=0.0)

    scenario: Mapped["Scenario"] = relationship(back_populates="products")
    recipe_items: Mapped[list["RecipeItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES), nullable=False
    )
    purchase_unit: Mapped[Unit] = mapped_column(
        SqlEnum(Unit, native_enum=False), nullable=False
    )
    unit_size: Mapped[float] = mapped_column(nullable=False, default=1.0)

    scenario: Mapped["Scenario"] = relationship(back_populates="ingredients")
    recipe_items: Mapped[list["RecipeItem"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True
    )
    quantity: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[Unit] = mapped_column(SqlEnum(Unit, native_enum=False), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="recipe_items")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_items")


class TrafficAssumption(Base):
    __tablename__ = "traffic_assumptions"

    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), primary_key=True
    )
    daily_customers: Mapped[int] = mapped_column(nullable=False)
    avg_products_per_customer: Mapped[float] = mapped_column(
        nullable=False, default=1.0
    )

    scenario: Mapped["Scenario"] = relationship(back_populates="traffic_assumption")


class SeasonalityFactor(Base):
    __tablename__ = "seasonality_factors"

    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), primary_key=True
    )
    month: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    multiplier: Mapped[float] = mapped_column(nullable=False, default=1.0)

    scenario: Mapped["Scenario"] = relationship(back_populates="seasonality_factors")

    __table_args__ = (CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),)
