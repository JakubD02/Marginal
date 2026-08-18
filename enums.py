from enum import IntEnum, StrEnum

class CostCategory(StrEnum):
    RENT = "rent"
    SALARY = "salary"
    ZUS = "zus"
    UTILITIES = "utilities"
    TAX = "tax"
    INSURANCE = "insurance"
    OTHER = "other"


class Unit(StrEnum):
    """Units of measure - for the ingredient purchase unit and the unit in the recipe line item"""
    KG = "kg"
    GRAM = "g"
    LITER = "l"
    ML = "ml"
    PIECE = "piece"


class Month(IntEnum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12