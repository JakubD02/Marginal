import pytest

from marginal.enums import Unit
from marginal.units import convert


def test_convert_kg_to_grams():
    assert convert(1.0, Unit.KG, Unit.GRAM) == 1000


def test_convert_kg_to_dag():
    assert convert(1.0, Unit.KG, Unit.DAG) == 100


def test_convert_g_to_dag():
    assert convert(1.0, Unit.GRAM, Unit.DAG) == 0.1


def test_convert_ml_to_liters():
    assert convert(200, Unit.ML, Unit.LITER) == 0.2


def test_convert_the_same_unit():
    assert convert(100, Unit.GRAM, Unit.GRAM) == 100


def test_incompatible_dimensions():
    with pytest.raises(ValueError):
        convert(100, Unit.GRAM, Unit.LITER)
