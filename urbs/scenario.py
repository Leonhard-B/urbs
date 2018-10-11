from .model import *
import pdb


#Added by Leon in order to update constrains for altenrative scenarios
def alternative_scenario_stock_prices(prob):
    # change stock commodity prices
    pdb.set_trace()
    """
    stock_commodities_only=[]
    leo2=list(prob.commodity_dict["price"].keys())
    for i in leo2: (i[2]=="Stock"): prob.commodity["price"][key]=100
    
    co = prob.commodity
    """
    
    co=pd.DataFrame()
    co.from_dict(prob.commodity_dict)
    stock_commodities_only = (prob.commodity.index.get_level_values('Type') == 'Stock')
    prob.commodity.loc[stock_commodities_only, 'price'] *= 100
    prob.commodity_dict=prob.commodity.to_dict()
    prob.del_component(prob.def_costs)
    prob.def_costs = pyomo.Constraint(
        prob.cost_type,
        rule=def_costs_rule,
        doc='main cost function by cost type')
    return prob
