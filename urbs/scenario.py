from .model import *
import pdb
import time

#Added by Leon in order to update constrains for altenrative scenarios

def alternative_scenario_base (prob, reverse):
    return prob

def alternative_scenario_stock_prices(prob, reverse):
    # change stock commodity prices
    if not reverse:
        for x in tuple(prob.commodity_dict["price"].keys()): 
            if x[2]=="Stock": 
                prob.commodity_dict["price"][x]*=100
        prob.del_component(prob.def_costs)
        prob.def_costs = pyomo.Constraint(
            prob.cost_type,
            rule=def_costs_rule,
            doc='main cost function by cost type')
        return prob
    if reverse:
        for x in tuple(prob.commodity_dict["price"].keys()): 
            if x[2]=="Stock": 
                prob.commodity_dict["price"][x]*=0.01
        prob.del_component(prob.def_costs)
        prob.def_costs = pyomo.Constraint(
            prob.cost_type,
            rule=def_costs_rule,
            doc='main cost function by cost type')
        return prob
    
    
def alternative_scenario_co2_limit(prob, reverse):
    # change global CO2 limit
    if not reverse:
        prob.global_prop_dict["value"]["CO2 limit"]*=0.05
        prob.del_component(prob.res_global_co2_limit)
        prob.res_global_co2_limit = pyomo.Constraint(
            rule=res_global_co2_limit_rule,
            doc='total co2 commodity output <= Global CO2 limit')
        return prob
    if reverse:
        prob.global_prop_dict["value"]["CO2 limit"]*=20
        prob.del_component(prob.res_global_co2_limit)
        prob.res_global_co2_limit = pyomo.Constraint(
            rule=res_global_co2_limit_rule,
            doc='total co2 commodity output <= Global CO2 limit')
        return prob
    

def alternative_scenario_co2_tax_mid(prob, reverse):
    # change CO2 price in Mid
    if not reverse:
        prob.commodity_dict["price"][('Mid', 'CO2', 'Env')]=50
        prob.del_component(prob.def_costs)
        prob.def_costs = pyomo.Constraint(
            prob.cost_type,
            rule=def_costs_rule,
            doc='main cost function by cost type')
        return prob
    if reverse:
        prob.commodity_dict["price"][('Mid', 'CO2', 'Env')]=prob._data["commodity"]["price"][('Mid', 'CO2', 'Env')]
        prob.del_component(prob.def_costs)
        prob.def_costs = pyomo.Constraint(
            prob.cost_type,
            rule=def_costs_rule,
            doc='main cost function by cost type')
        return prob
    

def alternative_scenario_north_process_caps(prob, reverse):
    # change maximum installable capacity
    if not reverse:
        prob.process_dict["cap-up"][('North', 'Hydro plant')]*=0.5
        prob.process_dict["cap-up"][('North', 'Biomass plant')]*=0.25 
        prob.del_component(prob.def_process_capacity)
        prob.def_process_capacity = pyomo.Constraint(
            prob.pro_tuples,
            rule=def_process_capacity_rule,
            doc='total process capacity = inst-cap + new capacity')
        prob.del_component(prob.res_process_capacity)
        prob.res_process_capacity = pyomo.Constraint(
            prob.pro_tuples,
            rule=res_process_capacity_rule,
            doc='process.cap-lo <= total process capacity <= process.cap-up')   
        return prob
    if reverse:
        prob.process_dict["cap-up"][('North', 'Hydro plant')]*=2
        prob.process_dict["cap-up"][('North', 'Biomass plant')]*=4
        prob.del_component(prob.def_process_capacity)
        prob.def_process_capacity = pyomo.Constraint(
            prob.pro_tuples,
            rule=def_process_capacity_rule,
            doc='total process capacity = inst-cap + new capacity')
        prob.del_component(prob.res_process_capacity)
        prob.res_process_capacity = pyomo.Constraint(
            prob.pro_tuples,
            rule=res_process_capacity_rule,
            doc='process.cap-lo <= total process capacity <= process.cap-up')
        return prob


def alternative_scenario_no_dsm(prob, reverse):
    if not reverse:
        del_dsm(prob)
        return prob
    if reverse:
        recreate_dsm(prob)
        return prob


def alternative_scenario_all_together(prob, reverse):
    # combine all other scenarios
    if not reverse:
        prob = alternative_scenario_stock_prices(prob,0)
        prob = alternative_scenario_co2_limit(prob,0)
        prob = alternative_scenario_north_process_caps(prob,0)
        return prob
    if reverse:
        prob = alternative_scenario_stock_prices(prob,1)
        prob = alternative_scenario_co2_limit(prob,1)
        prob = alternative_scenario_north_process_caps(prob,1)
        return prob


        
#Möglichkeit: Lass Benutzer Scenario im Excel File erstellen, lade dieses, vergleiche die Daten mit prob und update prob, an den geänderten Stellen
def del_dsm (prob):
        #pdb.set_trace()
        # empty the DSM dataframe completely
        prob.dsm_dict=pd.DataFrame().to_dict()
        
        prob.del_component(prob.dsm_site_tuples)
        prob.del_component(prob.dsm_down_tuples)
        prob.dsm_site_tuples = pyomo.Set()
        prob.dsm_down_tuples = pyomo.Set()
        
        
        prob.del_component(prob.dsm_down)
        prob.del_component(prob.dsm_up)
        prob.dsm_down = pyomo.Var()
        prob.dsm_up = pyomo.Var()
        
        prob.del_component(prob.def_dsm_variables)
        prob.del_component(prob.res_dsm_upward)
        prob.del_component(prob.res_dsm_downward)
        prob.del_component(prob.res_dsm_maximum)
        prob.del_component(prob.res_dsm_recovery)
        
        prob.def_dsm_variables = pyomo.Constraint.Skip
        prob.res_dsm_upward = pyomo.Constraint.Skip
        prob.res_dsm_downward = pyomo.Constraint.Skip
        prob.res_dsm_maximum = pyomo.Constraint.Skip
        prob.res_dsm_recovery = pyomo.Constraint.Skip
        
        #The following lines cause 99% of work for the formation of this scenario
        prob.del_component(prob.res_vertex)
        prob.del_component(prob.res_vertex_index)   #If the size/the number of constraints change, index also has to be replaced!
        prob.res_vertex = pyomo.Constraint(
            prob.tm, prob.com_tuples,
            rule=res_vertex_rule,
            doc='storage + transmission + process + source + buy - sell == demand')
    
def change_dsm (prob):
    return prob
        
def upd_dsm_constraints (prob):
    return prob
        
def recreate_dsm (prob):
    #dsm_variables & vertex rule
    #pdb.set_trace()
    #insert all the constraints!
    prob.dsm_dict=prob._data["dsm"].to_dict()
    try:
        myset=tuple(prob.dsm_dict["delay"].keys())
    except KeyError:
        raise NotImplementedError("Could not rebuild base modell!")
    
    prob.del_component(prob.dsm_site_tuples_domain)
    prob.del_component(prob.dsm_site_tuples)
    prob.dsm_site_tuples = pyomo.Set(
        within=prob.sit*prob.com,
        initialize=myset,
        doc='Combinations of possible dsm by site, e.g. (Mid, Elec)')

    prob.del_component(prob.dsm_down_tuples_domain)
    prob.del_component(prob.dsm_down_tuples_domain_index_0)           
    prob.del_component(prob.dsm_down_tuples_domain_index_0_index_0)
    prob.del_component(prob.dsm_down_tuples)
    prob.dsm_down_tuples = pyomo.Set(
        within=prob.tm*prob.tm*prob.sit*prob.com,
        initialize=[(t, tt, site, commodity)
                    for (t, tt, site, commodity)
                    in dsm_down_time_tuples(prob.timesteps[1:],
                                            prob.dsm_site_tuples,
                                            prob)],
        doc='Combinations of possible dsm_down combinations, e.g. '
            '(5001,5003,Mid,Elec)')
    
    prob.del_component(prob.dsm_up_index)
    prob.del_component(prob.dsm_up) 
    prob.dsm_up = pyomo.Var(
        prob.tm, prob.dsm_site_tuples,
        within=pyomo.NonNegativeReals,
        doc='DSM upshift')
    
    prob.del_component(prob.dsm_down)
    prob.dsm_down = pyomo.Var(
        prob.dsm_down_tuples,
        within=pyomo.NonNegativeReals,
        doc='DSM downshift')

    prob.del_component(prob.def_dsm_variables_index)
    prob.del_component(prob.def_dsm_variables)
    del prob.def_dsm_variables
    prob.def_dsm_variables = pyomo.Constraint(
        prob.tm, prob.dsm_site_tuples,
        rule=def_dsm_variables_rule,
        doc='DSMup * efficiency factor n == DSMdo (summed)')
    
    prob.del_component(prob.res_dsm_upward_index)
    prob.del_component(prob.res_dsm_upward)
    del prob.res_dsm_upward
    prob.res_dsm_upward = pyomo.Constraint(
        prob.tm, prob.dsm_site_tuples,
        rule=res_dsm_upward_rule,
        doc='DSMup <= Cup (threshold capacity of DSMup)')
    
    prob.del_component(prob.res_dsm_downward_index)
    prob.del_component(prob.res_dsm_downward)
    del prob.res_dsm_downward
    prob.res_dsm_downward = pyomo.Constraint(
        prob.tm, prob.dsm_site_tuples,
        rule=res_dsm_downward_rule,
        doc='DSMdo (summed) <= Cdo (threshold capacity of DSMdo)')
    
    prob.del_component(prob.res_dsm_maximum)
    prob.del_component(prob.res_dsm_maximum_index)
    del prob.res_dsm_maximum
    prob.res_dsm_maximum = pyomo.Constraint(
        prob.tm, prob.dsm_site_tuples,
        rule=res_dsm_maximum_rule,
        doc='DSMup + DSMdo (summed) <= max(Cup,Cdo)')
    
    prob.del_component(prob.res_dsm_recovery)
    prob.del_component(prob.res_dsm_recovery_index)
    del prob.res_dsm_recovery
    prob.res_dsm_recovery = pyomo.Constraint(
        prob.tm, prob.dsm_site_tuples,
        rule=res_dsm_recovery_rule,
        doc='DSMup(t, t + recovery time R) <= Cup * delay time L')
    
    #The following lines cause 50% of rebuilding work
    prob.del_component(prob.res_vertex)
    prob.del_component(prob.res_vertex_index)
    prob.res_vertex = pyomo.Constraint(
        prob.tm, prob.com_tuples,
        rule=res_vertex_rule,
        doc='storage + transmission + process + source + buy - sell == demand')    

