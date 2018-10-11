from .model import *



#Added by Leon in order to update constrains for altenrative scenarios
def alternative_scenario_stock_prices(prob):
    # change stock commodity prices
    co = prob.commodity
    stock_commodities_only = (prob.commodity.index.get_level_values('Type') == 'Stock')
    prob.commodity.loc[stock_commodities_only, 'price'] *= 100
    prob.commodity_dict=prob.commodity.to_dict()
    prob.del_component(prob.def_costs)
    prob.def_costs = pyomo.Constraint(
        prob.cost_type,
        rule=def_costs_rule,
        doc='main cost function by cost type')
    return prob
