import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os
import pandas as pd
from random import random
from .data import COLORS
from .input import get_input
from .output import get_constants, get_timeseries
from .pyomoio import get_entity
from .util import is_string
import pdb


def threated_plotting_reporting(#prob, result_dir, sce,  report_tuples,
                                report_sites_name, timesteps, plot_tuples,
                                plot_sites_name, plot_periods):
    print ("Hallo")

    global num_threads  #Write this to data.py, s.t. this function can be outsourced
    lock.acquire()
    num_threads += 1
    lock.release()
    
    urbs_path = os.path.join(folder_in, subfolder, scenarios[scen]+dt_h5)
    helpdf = urbs.load(urbs_path)
        helpdf = helpdf._result
    
    # Filter results
    urbs_results[scen] = helpdf['e_pro_out'].unstack()
    
    # Get Elec data
    urbs_elec[scen] = urbs_results[scen]['Elec'].reorder_levels(['sit', 'pro', 't']).sort_index()
    urbs_elec_ts[scen] = urbs_elec[scen].unstack(level=0).unstack(level=0)
    urbs_elec_ts_ger[scen] = urbs_elec[scen].unstack(level=1).unstack(level=1).sum(axis=0).unstack().T.sum(axis=0)
    
    # Get CO2 data
    urbs_co2[scen] = urbs_results[scen]['CO2'].reorder_levels(['sit', 'pro', 't']).sort_index()
    urbs_co2_ts[scen] = urbs_co2[scen].unstack(level=0).unstack(level=0)
    urbs_co2_ts_ger[scen] = urbs_co2[scen].unstack(level=1).unstack(level=1).sum(axis=0).unstack().T.sum(axis=0)
    
    # Get Transmission data
    urbs_tra[scen] = helpdf['cap_tra'].unstack()
    urbs_tra_new[scen] = helpdf['cap_tra_new'].unstack()
    urbs_tra_e_in[scen] = helpdf['e_tra_in']
    urbs_tra_e_out[scen] = helpdf['e_tra_out']
    
    # Get process capacities
    urbs_cap[scen] = helpdf['cap_pro'].unstack()
    urbs_cap_new[scen] = helpdf['cap_pro_new'].unstack()
    
    # Get curtailment data
    urbs_curt[scen] = helpdf['e_pro_in'].unstack(level=3)['Elec'].unstack(level=2)['Curtailment'].unstack(level=1)

    # Get storage data
    urbs_sto_in[scen] = helpdf['e_sto_in']
    urbs_sto_out[scen] = helpdf['e_sto_out']
    
    # Get scenario costs
    urbs_cost[scen] = helpdf['costs']
    
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
    prob = scenario(prob, True, filename)
    
    lock.acquire()
    num_threads -= 1
    lock.release()
