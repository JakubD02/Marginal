from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.schemas import ScenarioExport
from marginal.schemas.fixed_cost import FixedCostExport
from marginal.schemas.ingredient import IngredientExport
from marginal.schemas.product import ProductExport
from marginal.schemas.seasonality_factor import SeasonalityFactorExport
from marginal.schemas.traffic_assumption import TrafficAssumptionExport


def export_scenario_to_json(scenario_name: str):
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)
        exported_data = ScenarioExport(
            name=scenario.name,
            currency=scenario.currency,
            working_days_per_month=scenario.working_days_per_month,
            fixed_costs=[
                FixedCostExport.model_validate(x) for x in scenario.fixed_costs
            ],
            products=[ProductExport.model_validate(x) for x in scenario.products],
            ingredients=[
                IngredientExport.model_validate(x) for x in scenario.ingredients
            ],
            traffic=(
                TrafficAssumptionExport.model_validate(scenario.traffic_assumption)
                if scenario.traffic_assumption
                else None
            ),
            seasonality=[
                SeasonalityFactorExport.model_validate(x)
                for x in scenario.seasonality_factors
            ],
        )

        json_output = exported_data.model_dump_json(indent=3)

        with open("scenario_export.json", "w", encoding="utf-8") as f:
            f.write(json_output)
