from marginal.calculations import run_simulation
from marginal.cli.helpers import _get_scenario_or_exit
from marginal.database import get_session
from marginal.presenters import render_simulation


def simulate(scenario_name: str):
    """Run full simulation for scenario"""
    with get_session() as session:
        scenario = _get_scenario_or_exit(session, scenario_name)

        result = run_simulation(scenario)
        render_simulation(result)
