from calculations import compute_unit_cost
from database import get_session
from repository import get_products_by_scenario, get_scenario_by_name


with get_session() as session:
    scenario = get_scenario_by_name(session, "Ice cream parlor 59")
    products = get_products_by_scenario(session, scenario.id)
    for p in products:
        cost = compute_unit_cost(p)
        print(f"{p.name}: cost={cost:.2f} {scenario.currency}, price={p.price}, margin={p.price - cost:.2f}")