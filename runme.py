import os
import pandas as pd
import pyomo.environ
import shutil
import urbs
from datetime import datetime
from pyomo.opt.base import SolverFactory
from urbs.modelhelper import *
#remove prob @prob=run_scenario() and result @result=optim.solve()
#in plot.py: import erst in Funktion??

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
    co.loc[stock_commodities_only, 'price'] *= 1.5
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
    now = datetime.now().strftime('%Y%m%dT%H%M%S')

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
    elif optim.name == 'cplex':
        optim.set_options("log={}".format(logfile))
    else:
        print("Warning from setup_solver: no options set for solver "
              "'{}'!".format(optim.name))
    return optim


def run_alternative_scenario(prob, timesteps, scenario, result_dir, dt,
                 plot_tuples=None,  plot_sites_name=None, plot_periods=None,
                 report_tuples=None, report_sites_name=None):
 
    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    
    t1=time.time()
    run=20
    print (run)
    while run:
        run=run-1
        if str(sce).find("alternative_scenario_new_timeseries") >=0:
            global timeseries_number
            #sce=sce+str(timeseries_number.pop())
            filename=os.path.join("input", "{}.xlsx").format(sce)
            prob=urbs.alternative_scenario_new_timeseries_(prob, 0, filename)
        else:
            prob=scenario(prob, 0)
    t2=time.time()
    print (t2-t1)
    return prob
    
    
def run_scenario(input_file, timesteps, scenario, result_dir, dt,
                 plot_tuples=None,  plot_sites_name=None, plot_periods=None,
                 report_tuples=None, report_sites_name=None):
    """ run an urbs model for given input, time steps and scenario

    Args:
        data: content of the excel sheet
        input_file: filename to an Excel spreadsheet for urbs.read_excel             #changed to data
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
    
    data = urbs.read_excel(input_file)
    #klone Objekt, um Daten nicht erneut auslesen zu müssen
    t1=time.time()
    run=2
    print (run)
    while run:
        run=run-1
        data2 = deepcopy(data)
        data2 = scenario(data2)
        #urbs.validate_input(data2)
        #urbs.validate_input(data)
        #t2=time.time()
        #print (t2-t1)
        #t1=time.time()
        
        # create model
        prob = urbs.create_model(data, dt, timesteps)
    t2=time.time()
    print (t2-t1)
    t1=time.time()
    



if __name__ == '__main__':
    print ("Load Data + Validation \ncreate model \nwrite .lp \nsetup solver + solve \nwrite .h5 \nplot + report")
    #process = psutil.Process(os.getpid())
    mylist=list()
    #interval = rupt.setInterval(rupt.myfunc, 1, process, mylist) # Does not record Solver workspace
    #print("Aktuelle Speicherbelegung: " + str(process.memory_info().rss/1000000) + " MB\n")
    #start_time=time.time()
    #start_time_proc=time.time()
    #Speicherbelegung=list()
    #Speicherbelegung.append(process.memory_info().rss/1000000)

    input_file = 'mimo-example.xlsx'
    result_name = os.path.splitext(input_file)[0]  # cut away file extension
    result_dir = prepare_result_directory(result_name)  # name + time stamp

    # copy input file to result directory
    shutil.copyfile(input_file, os.path.join(result_dir, input_file))
    # copy runme.py to result directory
    shutil.copy(__file__, result_dir)

    # simulation timesteps
    #(offset, length) = (0, 500)  # time step selection
    offset_list=[0]
    lenght_list = [500] #[500,400,300,200,100,90,80,70,60, 50, 40, 30, 20,10,9,8,7,6,5,4,3,2]
    #timesteps = range(offset, offset+length+1)
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
    #plot_periods = {
    #    'all': timesteps[1:]
    #}

    # add or change plot colors
    my_colors = {
        'South': (230, 200, 200),
        'Mid': (200, 230, 200),
        'North': (200, 200, 230)}
    for country, color in my_colors.items():
        urbs.COLORS[country] = color
    
    timeseries_number=[]       #Helper number used for global declaration of current timeseries sheet
    # select scenarios to be run
    #normal scenarios must be last, since the base model would be destroyed
    scenarios = [
        scenario_base
        , urbs.alternative_scenario_new_timeseries (timeseries_number, 1)
        # ,urbs.alternative_scenario_no_dsm
        # ,urbs.alternative_scenario_new_timeseries(timeseries_number,1)
        # ,urbs.alternative_scenario_new_timeseries(timeseries_number,2)
        # ,urbs.alternative_scenario_new_timeseries(timeseries_number,"Leon")
        # ,urbs.alternative_scenario_co2_tax_mid
        # ,urbs.alternative_scenario_co2_limit
        # ,urbs.alternative_scenario_no_dsm
        # ,urbs.alternative_scenario_north_process_caps
        # ,urbs.alternative_scenario_stock_prices
        # ,urbs.alternative_scenario_all_together
        
        # ,scenario_co2_tax_mid
        # ,scenario_co2_limit
        # ,scenario_no_dsm
        # ,scenario_north_process_caps
        # ,scenario_stock_prices
        # ,scenario_all_together
        ]
    
    #load Data from Excel sheet
    #data = urbs.read_excel(input_file)
    #urbs.validate_input(data)
    
    
    for scenario in scenarios:
        #Speicherbelegung.append(process.memory_info().rss/1000000)
        #t1=time.time()
        #szenario_start_time=time.time()
        
        # Set new Offset
        if offset_list:
            offset=offset_list.pop()
            print ("offset: " + str(offset))
            # alternative scenarios need a new base model
            if str(scenario.__name__).find("alternative") >=0:
                try:
                    del prob # prob will be redefined later with correct offset & timestep
                except NameError:
                    pass
        
        # if list is not empty: take the new value from the time list and set new timesteps
        if lenght_list:
            timesteps=range(offset, offset + lenght_list.pop() + 1)
            print ("timesteps: " + str (timesteps))
            if str(scenario.__name__).find("alternative") >=0:
                try:
                    del prob
                except NameError:
                    pass

        if len(timesteps)<=168:
            plot_periods = {'all': timesteps[1:]}
        else:
            plot_periods = {'all': timesteps[1:168]}
        
        #Falls es ein alternatives Szenario ist, soll run_alternative_scenario aufgerufen werden und das prob_no_dsm verwendet werden
        if str(scenario.__name__).find("alternative")>=0: #or str(scenario.__name__).find("base")>=0:  Warum habe ich das dazu geschrieben?
            try: 
                prob
            except NameError:
                data = urbs.read_excel(input_file)
                prob = urbs.create_model(data, dt, timesteps)
            prob = run_alternative_scenario (prob, timesteps, scenario, result_dir, dt,
                            plot_tuples=plot_tuples,
                            plot_sites_name=plot_sites_name,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples,
                            report_sites_name=report_sites_name)
        else:
            run_scenario(input_file, timesteps, scenario, result_dir, dt,
                            plot_tuples=plot_tuples,
                            plot_sites_name=plot_sites_name,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples,
                            report_sites_name=report_sites_name)

        #t2=time.time()
        #print (str(scenario.__name__) + ": " + str(t2-t1))
        #current_time=time.time()
        #print (
            #"\nZeit seit Start: " +str(current_time-start_time) +"s" +
            #"\nRechenzeit seit Start: "+str(t2-start_time_proc)+"s" +
            #"\nZeit für Szenario: "+str(current_time-szenario_start_time)+"s\n"+
            #"Rechenzeit für " + str(i+1) + " Szenarios: "+str(t2-t1)+"s"
            #+"\nAktuelle Speicherbelegung: " + str(process.memory_info().rss/1000000) + " MB\n"
            #)
        

        
    #Speicherbelegung.append(process.memory_info().rss/1000000)
    #print (Speicherbelegung)
    #interval.cancel() 
    #for x in range(len(mylist)):
    #    print (mylist[x])