import os
import pandas as pd
import pyomo.environ
import shutil
import urbs
from datetime import datetime
from pyomo.opt.base import SolverFactory
#delete m._data (some functions need to be altered), remove prob @prob=run_scenario() and result @result=optim.solve()

#Breakpoints
import pdb   

#Memory usage
import psutil

#Time measurment
import time

#for proper copying of data
from copy import deepcopy

#Interrupt
import interrupt_timer as rupt

# SCENARIOS
def scenario_base(data):
    # do nothing
    return data


def scenario_stock_prices(data):
    # change stock commodity prices
    co = data['commodity']
    stock_commodities_only = (co.index.get_level_values('Type') == 'Stock')
    co.loc[stock_commodities_only, 'price'] *= 100
    return data


def scenario_co2_limit(data):
    # change global CO2 limit
    global_prop = data['global_prop']
    global_prop.loc['CO2 limit', 'value'] *= 0.05
    return data


def scenario_co2_tax_mid(data):
    # change CO2 price in Mid
    co = data['commodity']
    co.loc[('Mid', 'CO2', 'Env'), 'price'] = 50
    return data


def scenario_north_process_caps(data):
    # change maximum installable capacity
    pro = data['process']
    pro.loc[('North', 'Hydro plant'), 'cap-up'] *= 0.5
    pro.loc[('North', 'Biomass plant'), 'cap-up'] *= 0.25
    return data


def scenario_no_dsm(data):
    # empty the DSM dataframe completely
    data['dsm'] = pd.DataFrame()
    return data


def scenario_all_together(data):
    # combine all other scenarios
    data = scenario_stock_prices(data)
    data = scenario_co2_limit(data)
    data = scenario_north_process_caps(data)
    return data


def prepare_result_directory(result_name):
    """ create a time stamped directory within the result folder """
    # timestamp for result directory
    now = datetime.now().strftime('%Y%m%dT%H%M')

    # create result directory if not existent
    result_dir = os.path.join('result', '{}-{}'.format(result_name, now))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    return result_dir


def setup_solver(optim, logfile='solver.log'):
    """ """
    if optim.name == 'gurobi':
        # reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
        optim.set_options("logfile={}".format(logfile))
        # optim.set_options("timelimit=7200")  # seconds
        # optim.set_options("mipgap=5e-4")  # default = 1e-4
    elif optim.name == 'glpk':
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    else:
        print("Warning from setup_solver: no options set for solver "
              "'{}'!".format(optim.name))
    return optim


def run_alternative_scenario(prob, timesteps, scenario, result_dir, dt,
                 plot_tuples=None,  plot_sites_name=None, plot_periods=None,
                 report_tuples=None, report_sites_name=None):
 
    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    prob=scenario(prob, 0)
    #urbs.validate_input(data)
    
    # refresh time stamp string and create filename for logfile
    now = prob.created
    log_filename = os.path.join(result_dir, '{}.log').format(sce)

    #Write model to lp File
    model_filename = os.path.join(result_dir, '{}.lp').format(sce)
    prob.write(model_filename, io_options={"symbolic_solver_labels":True})
    
    # solve model and read results
    optim = SolverFactory('glpk')  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=False)

    # save problem solution (and input data) to HDF5 file
    urbs.save(prob, os.path.join(result_dir, '{}.h5'.format(sce)))

    # write report to spreadsheet
    urbs.report(
        prob,
        os.path.join(result_dir, '{}.xlsx').format(sce),
        report_tuples=report_tuples,
        report_sites_name=report_sites_name)

    # result plots
    urbs.result_figures(
        prob,
        os.path.join(result_dir, '{}'.format(sce)),
        timesteps,
        plot_title_prefix=sce.replace('_', ' '),
        plot_tuples=plot_tuples,
        plot_sites_name=plot_sites_name,
        periods=plot_periods,
        figure_size=(24, 9))
    prob==scenario(prob, 1)
    return prob
    
    
def run_scenario(data, timesteps, scenario, result_dir, dt,
                 plot_tuples=None,  plot_sites_name=None, plot_periods=None,
                 report_tuples=None, report_sites_name=None):
    """ run an urbs model for given input, time steps and scenario

    Args:
        data: content of the excel sheet
        input_file: filename to an Excel spreadsheet for urbs.read_excel             #geändert zu data
        timesteps: a list of timesteps, e.g. range(0,8761)
        scenario: a scenario function that modifies the input data dict
        result_dir: directory name for result spreadsheet and plots
        dt: length of each time step (unit: hours)
        plot_tuples: (optional) list of plot tuples (c.f. urbs.result_figures)
        plot_sites_name: (optional) dict of names for sites in plot_tuples
        plot_periods: (optional) dict of plot periods(c.f. urbs.result_figures)
        report_tuples: (optional) list of (sit, com) tuples (c.f. urbs.report)
        report_sites_name: (optional) dict of names for sites in report_tuples

    Returns:
        the urbs model instance
    """
    
    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    #klone Objekt, um Daten nicht erneut auslesen zu müssen
    data2=deepcopy(data)
    data2 = scenario(data2)
    urbs.validate_input(data2)
       
    # create model
    prob = urbs.create_model(data2, dt, timesteps)
    
    #Write model to lp File
    model_filename = os.path.join(result_dir, '{}.lp').format(sce)
    prob.write(model_filename, io_options={"symbolic_solver_labels":True})
    
    # refresh time stamp string and create filename for logfile
    now = prob.created
    log_filename = os.path.join(result_dir, '{}.log').format(sce)
    
    # solve model and read results
    optim = SolverFactory('glpk')  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=False)

    # save problem solution (and input data) to HDF5 file
    urbs.save(prob, os.path.join(result_dir, '{}.h5'.format(sce)))

    # write report to spreadsheet
    urbs.report(
        prob,
        os.path.join(result_dir, '{}.xlsx').format(sce),
        report_tuples=report_tuples,
        report_sites_name=report_sites_name)

    # result plots
    urbs.result_figures(
        prob,
        os.path.join(result_dir, '{}'.format(sce)),
        timesteps,
        plot_title_prefix=sce.replace('_', ' '),
        plot_tuples=plot_tuples,
        plot_sites_name=plot_sites_name,
        periods=plot_periods,
        figure_size=(24, 9))
    return prob


if __name__ == '__main__':
    process = psutil.Process(os.getpid())
    mylist=list()
    #interval = rupt.setInterval(rupt.myfunc, 1, process, mylist)
    print("Aktuelle Speicherbelegung: " + str(process.memory_info().rss/1000000) + " MB\n")
    start_time=time.time()
    start_time_proc=time.process_time()
    Speicherbelegung=list()
    Speicherbelegung.append(process.memory_info().rss/1000000)
    
    input_file = 'mimo-example.xlsx'
    result_name = os.path.splitext(input_file)[0]  # cut away file extension
    result_dir = prepare_result_directory(result_name)  # name + time stamp

    # copy input file to result directory
    shutil.copyfile(input_file, os.path.join(result_dir, input_file))
    # copy runme.py to result directory
    shutil.copy(__file__, result_dir)

    # simulation timesteps
    (offset, length) = (3500, 3)  # time step selection
    timesteps = range(offset, offset+length+1)
    dt = 1  # length of each time step (unit: hours)

    
    # plotting commodities/sites
    plot_tuples = [
        ('North', 'Elec'),
        ('Mid', 'Elec'),
        ('South', 'Elec'),
        (['North', 'Mid', 'South'], 'Elec')]

    # optional: define names for sites in plot_tuples
    plot_sites_name = {('North', 'Mid', 'South'): 'All'}

    # detailed reporting commodity/sites
    report_tuples = [
        ('North', 'Elec'), ('Mid', 'Elec'), ('South', 'Elec'),
        ('North', 'CO2'), ('Mid', 'CO2'), ('South', 'CO2')]

    # optional: define names for sites in report_tuples
    report_sites_name = {'North': 'Greenland'}

    # plotting timesteps
    plot_periods = {
        'all': timesteps[1:]
    }

    # add or change plot colors
    my_colors = {
        'South': (230, 200, 200),
        'Mid': (200, 230, 200),
        'North': (200, 200, 230)}
    for country, color in my_colors.items():
        urbs.COLORS[country] = color

    # select scenarios to be run
    scenarios = [
        scenario_base
        ,urbs.alternative_scenario_no_dsm
        #,urbs.alternative_scenario_all_together
        #,urbs.alternative_scenario_north_process_caps
        #,urbs.alternative_scenario_stock_prices
        #,urbs.alternative_scenario_co2_tax_mid
        #,urbs.alternative_scenario_co2_limit
        #,scenario_co2_tax_mid
        ,scenario_no_dsm
        #,scenario_north_process_caps
        #,scenario_co2_limit
        #,scenario_co2_tax_mid
        #,scenario_all_together
        #,scenario_stock_prices
        ]
    
    #load Data from Excel sheet
    data = urbs.read_excel(input_file)

    
    for scenario in scenarios:
        Speicherbelegung.append(process.memory_info().rss/1000000)
        t1=time.process_time()
        szenario_start_time=time.time()
        
        #Falls es ein alternatives Szenario ist, soll run_alternative_scenario aufgerufen werden und das prob_base verwendet werden
        if str(scenario.__name__).find("alternative")>=0:
            #prob=prob_base.clone()
            prob = run_alternative_scenario (prob, timesteps, scenario, result_dir, dt,
                            plot_tuples=plot_tuples,
                            plot_sites_name=plot_sites_name,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples,
                            report_sites_name=report_sites_name)
        else:
             prob = run_scenario(data, timesteps, scenario, result_dir, dt,
                            plot_tuples=plot_tuples,
                            plot_sites_name=plot_sites_name,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples,
                            report_sites_name=report_sites_name)
        
        t2=time.process_time()
        current_time=time.time()
        print (
            "\nZeit seit Start: " +str(current_time-start_time) +"s" +
            "\nRechenzeit seit Start: "+str(t2-start_time_proc)+"s" +
            "\nZeit für Szenario: "+str(current_time-szenario_start_time)+"s"+
            "\nRechenzeit für Szenario: "+str(t2-t1)+"s"+
            "\nAktuelle Speicherbelegung: " + str(process.memory_info().rss/1000000) + " MB\n")
        
        #Die alternativen Szenarien benötigen das Basis Modell      #Bei neuen alt. Szenarien nicht mehr notwendig: Klonen wird vermieden!
        #if scenario.__name__ == "scenario_base":
        #    prob_base=prob.clone()
    sce = scenario.__name__
    model_filename = os.path.join(result_dir, '{rebuilt_base}.lp').format(sce)
    prob.write(model_filename, io_options={"symbolic_solver_labels":True})
    Speicherbelegung.append(process.memory_info().rss/1000000)
    print (Speicherbelegung)
#    interval.cancel() 
#    for x in range(len(mylist)):
#        print (mylist[x])