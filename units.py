"""Unit conversion for ingredient quantities"""

from enums import Unit

_MASS = {Unit.KG, Unit.DAG, Unit.GRAM}
_VOLUME = {Unit.LITER, Unit.ML}
_COUNT = {Unit.PIECE}


_BASE = {
    Unit.KG: 1000,
    Unit.DAG: 10,
    Unit.GRAM: 1,
    Unit.LITER: 1000,
    Unit.ML: 1,
    Unit.PIECE: 1,
}


def same_dimension(a: Unit, b: Unit) -> bool:
    """Check whether two units belong to the same dimension"""
    for group in (_MASS, _VOLUME, _COUNT):
        if a in group and b in group:
            return True
    return False


def convert(quantity: float, from_unit: Unit, to_unit: Unit) -> float | None:
    """Convert quantity from one unit to another

    Examples:
        >>> convert(1.0, Unit.KG, Unit.G)
        1000
    """
    if from_unit == to_unit:
        return quantity

    if not same_dimension(from_unit, to_unit):
        raise ValueError(
            f"Cannot convert {from_unit} to {to_unit} - dimension is different."
        )

    conversion_factor = _BASE[from_unit] / _BASE[to_unit]
    return conversion_factor * quantity
