from __future__ import division
import numpy as np
import pymc as pm
import matplotlib.pyplot as plt
from copy import copy
import matplotlib.pyplot as plt
import numpy.lib.recfunctions as rec
import os.path
import os
from ordereddict import OrderedDict

import hddm

def load_scalp_data(continuous=True, remove_outliers=.4, shift_theta=False):
    import numpy.lib.recfunctions as rec
    subjs = range(1,15)
    if continuous:
        file_prefix = 'data/theta_continuous/m3tst3_auc_'
        dtype = np.dtype([('subj_idx', np.int), ('stim', 'S8'), ('rt', np.float), ('response', np.float), ('prer1', np.float), ('prer2', np.float), ('theta', np.float), ('cue2', np.float), ('dbs', np.int)])

    else:
        file_prefix = 'data/theta/m3tst3_auc_'
        dtype = np.dtype([('subj_idx', np.int), ('stim', 'S8'), ('rt', np.float), ('response', np.float), ('prer1', np.float), ('prer2', np.float), ('theta', 'S8'), ('cue2', np.float), ('dbs', np.int)])

    all_data = []
    for subj_idx, subj in enumerate(subjs):
        for onoff in ['on', 'off']:
            data = np.recfromtxt(file_prefix+str(subj)+onoff+'.txt', dtype=dtype)
            data['subj_idx'] = subj_idx

            if continuous: # Normalize theta
                mu = np.mean(data['theta'])
                sigma = np.std(data['theta'])
                data['theta'] = (data['theta']-mu)/sigma
                if shift_theta:
                    # Shift the theta values one back
                    tmp = copy(data['theta'][:-1])
                    data['theta'][1:] = tmp
                    data = data[1:]

            all_data.append(data)

    all_data = np.concatenate(all_data)
    all_data = rec.append_fields(all_data,
                                 data=(all_data['stim'], all_data['dbs'], all_data['dbs'], all_data['dbs']),
                                 names=('conf', 'dbs_effect', 'dbs_effect_inv', 'dbs_inv'),
                                 usemask=False)
    
    # Remove outliers
    if remove_outliers:
        all_data = all_data[all_data['rt']>remove_outliers]
    # Set names for stim, theta and dbs
    all_data['conf'][all_data['conf'] == '1'] = 'HC'
    all_data['conf'][all_data['conf'] == '2'] = 'HC'
    all_data['conf'][all_data['conf'] == '3'] = 'LC'
    all_data['stim'][all_data['stim'] == '1'] = 'WW'
    all_data['stim'][all_data['stim'] == '2'] = 'LL'
    all_data['stim'][all_data['stim'] == '3'] = 'WL'

    #all_data['theta'][all_data['theta'] == '0'] = 'low'
    #all_data['theta'][all_data['theta'] == '1'] = 'high'

    all_data['dbs_effect'][all_data['dbs_effect'] == 0] = -1
    all_data['dbs_effect_inv'] = -all_data['dbs_effect']
    all_data['dbs_inv'] = 1-all_data['dbs']
        
    return all_data

def load_intraop_data(continuous=True):
    subjs = range(1,9)
    file_prefix = 'data/stn/inoptst3_'
    all_data = []

    dtype = np.dtype([('subj_idx', np.int), ('stim', 'S8'), ('rt', np.float), ('response', np.float), ('vent', np.float), ('mid', np.float), ('dors', np.float)])

    for subj_idx,subj in enumerate(subjs):
        data = np.recfromtxt(file_prefix+str(subj)+'.txt', dtype=dtype)
        data['subj_idx'] = subj_idx
        valid_rows = data['response'] != 10000
        data = data[valid_rows]
        if continuous: # Normalize theta
            for col in ('vent', 'mid', 'dors'):
                mu = np.mean(data[col])
                sigma = np.std(data[col])
                data[col] = (data[col]-mu)/sigma
        all_data.append(data)

    all_data = np.concatenate(all_data)

    all_data = rec.append_fields(all_data, names=('conf',),
                                 data=(all_data['stim'],), dtypes=('S8', np.int, np.int), usemask=False)
    # Remove outliers
    all_data = all_data[all_data['rt']>.4]
    # Set names for stim, theta and dbs
    all_data['conf'][all_data['stim'] == '3'] = 'HC'
    all_data['conf'][all_data['stim'] == '4'] = 'LC'
    all_data['conf'][all_data['stim'] == '5'] = 'HC'
    all_data['stim'][all_data['stim'] == '3'] = 'WW'
    all_data['stim'][all_data['stim'] == '4'] = 'WL'
    all_data['stim'][all_data['stim'] == '5'] = 'LL'
    
    return all_data

def create_models_pd():
    # Load data
    data_pd = np.recfromcsv('PD_PS.csv')
    data_dbs_off = data_pd[data_pd['dbs'] == 0]
    data_dbs_on = data_pd[data_pd['dbs'] == 1]

    models = OrderedDict()
    # Create PD models
    for dbs in ['dbs', 'dbs_effect', 'dbs_inv', 'dbs_inv_effect']:
        models['PD_stim_v_%s'%dbs] = {'data': data_pd, effects_on:{'a':['theta',dbs]}, 'depends_on':{'v':'stim', 'e_theta_a':'conf', 'e_inter_theta_%s_a'%dbs:'conf'}}
        models['PD_%s'%dbs] = {'data': data_pd, effects_on:{'a':['theta',dbs]}, 'depends_on':{'e_theta_a':'conf', 'e_inter_theta_%s_a'%dbs:'conf'}}

    models['dbs_off_PD_paper'] = {'data': data_dbs_off, effects_on:{'a':'theta'}, 'depends_on':{'v':['stim'], 'e_theta_a':['conf']}}
    models['dbs_on_PD_paper'] = {'data': data_dbs_on, effects_on:{'a':'theta'}, 'depends_on':{'v':['stim'], 'e_theta_a':['conf']}}

    return models

def load_datasets(path=None):
    # Load data
    if path is None:
        path = '.'
    data_diss = load_csv_jim(os.path.join(path, 'DissData_P01.csv'))
    data_sen =  load_csv_jim(os.path.join(path, 'DBSC_N15_P03.csv'))
    data_easy = load_csv_jim(os.path.join(path, 'DBSC_N15_EASY.csv'))
    data_pd = hddm.utils.load_csv(os.path.join(path, 'PD_PS.csv'))
    data_pd = add_median_fields(data_pd)

    data_pd_dbs_off = data_pd[data_pd['dbs'] == 0]
    data_pd_dbs_on = data_pd[data_pd['dbs'] == 1]

    data_combined = np.concatenate((data_diss, data_sen))
    group_col = np.empty(data_combined.shape, dtype=[('group', np.int)])
    group_col['group'][:len(data_diss)] = 0
    group_col['group'][len(data_diss):] = 1
    data_combined = rec.append_fields(data_combined, names=['group'],
                                      data=[group_col], dtypes=[np.int], usemask=False)

    datasets = [data_diss, data_sen, data_easy, data_pd_dbs_off, data_pd_dbs_on, data_combined]
    names = ['data_diss', 'data_sen', 'data_easy', 'data_pd_dbs_off', 'data_pd_dbs_on', 'data_combined']
    
    return datasets, names

def create_models_nodbs(path=None, full=False):
    datasets, names = load_datasets(path=path)

    models = []
    model_types = ['simple']
    if full:
        model_types.append('full')
        
    effects_on = ['a']
    vs_on = ['conf']
    e_thetas_on = [['stim'], ['conf']]
    excludes = [['T'], ['Z'], ['T','Z'], []]
    
    for name,data in zip(names, datasets):
        for effect in effects_on:
            for e_theta_on in e_thetas_on:
                  for v_on in vs_on:
                    models.append({'data': data, 'name':name,
                                   'effects_on':{effect: 'theta'},
                                   'depends_on':{'v':vs_on, 'e_theta_'+effect:e_theta_on}})
                    models.append({'data': data, 'name':name,
                                   'effects_on':{effect:'theta'},
                                   'depends_on':{'v':vs_on, 'e_theta_'+effect:e_theta_on, 'a':['stim']}})

                    for col in ['conf_effect', 'LL_effect', 'WW_effect']:
                        models.append({'data': data, 'name':name,
                                       'effects_on': {effect: ['theta', col]},
                                       'depends_on': {'v':vs_on}})

                    if full:
                        for exclude in excludes:
                            for col in ['conf_effect', 'LL_effect', 'WW_effect']:
                                models.append({'data': data, 'name':name,
                                               'effects_on': {effect: ['theta', col]},
                                               'depends_on': {'v':vs_on},
                                               'model_type': 'full', 'exclude':exclude})
                                
                        models.append({'data': data, 'name':name,
                                       'effects_on': {effect: 'theta'},
                                       'depends_on': {'e_theta_'+effect:e_theta_on},
                                       'model_type': 'full', 'exclude':exclude})
  
    return models


def create_models2(path=None, full=False):
    # Load data
    if path is None:
        path = '.'

    datasets, names = load_datasets(path=path)
    
    models = []
    model_types = ['simple']
    if full:
        model_types.append('full')
        
    effects_on = ['a']
    vs_on = ['conf']
    e_thetas_on = [['stim'], ['conf']]
    excludes = [['T'], ['Z'], ['T','Z'], []]
    
    for name,data in zip(names, datasets):
        for effect in effects_on:
            for e_theta_on in e_thetas_on:
                  for v_on in vs_on:
                    models.append({'data': data, 'name':name,
                                   'effects_on':{effect: 'theta'},
                                   'depends_on':{'v':vs_on, 'e_theta_'+effect:e_theta_on}, 'use_root_for_effects':True})
                    models.append({'data': data, 'name':name,
                                   'effects_on':{effect:'theta'},
                                   'depends_on':{'v':vs_on, 'e_theta_'+effect:e_theta_on, 'a':['stim']}, 'use_root_for_effects':True})

                    for col in ['conf_effect', 'LL_effect', 'WW_effect']:
                        models.append({'data': data, 'name':name,
                                       'effects_on': {effect: ['theta', col]},
                                       'depends_on': {'v':vs_on}, 'use_root_for_effects':True})
                        models.append({'data': data, 'name':name,
                                       'effects_on': {effect: ['theta', col]},
                                       'depends_on': {'v':vs_on, 'a':'stim'}, 'use_root_for_effects':True})


                    if full:
                        for exclude in excludes:
                            for col in ['conf_effect', 'LL_effect', 'WW_effect']:
                                models.append({'data': data, 'name':name,
                                               'effects_on': {effect: ['theta', col]},
                                               'depends_on': {'v':vs_on},
                                               'model_type': 'full', 'exclude':exclude, 'use_root_for_effects':True})
                                models.append({'data': data, 'name':name,
                                               'effects_on': {effect: ['theta', col]},
                                               'depends_on': {'v':vs_on, 'a':'stim'},
                                               'model_type': 'full', 'exclude':exclude, 'use_root_for_effects':True})
                                
                        models.append({'data': data, 'name':name,
                                       'effects_on': {effect: 'theta'},
                                       'depends_on': {'e_theta_'+effect:e_theta_on},
                                       'model_type': 'full', 'exclude':exclude, 'use_root_for_effects':True})
  
    return models

def load_models(pd=False, full=False):
    if pd:
        jobs = create_jobs_pd()
    elif full_mc:
        jobs = create_jobs_full()
    else:
        jobs = create_jobs()

    models = OrderedDict()
    for name, params in jobs.iteritems():
        models[name] = run_model(name, params, load=True)

    return models

def add_median_fields(data):
    theta_median = np.empty(data.shape, dtype=[('theta_split','S8')])
    rt_split_cor_inc = np.empty(data.shape, dtype=[('rt_split_cor_inc','S8')])
    rt_split = np.empty(data.shape, dtype=[('rt_split','S8')])

    for subj in np.unique(data['subj_idx']):
        subj_idx = data['subj_idx']==subj

        # Set median
        med = np.median(data[subj_idx]['theta'])
        theta_median[subj_idx & (data['theta'] < med)] = 'low'
        theta_median[subj_idx & (data['theta'] >= med)] = 'high'

        # Set high/low RT
        cor_idx = data['response']==1
        inc_idx = data['response']==0
        med_cor = np.median(data[subj_idx & cor_idx]['rt'])
        med_inc = np.median(data[subj_idx & inc_idx]['rt'])
        med = np.median(data[subj_idx]['rt'])

        rt_split_cor_inc[subj_idx & cor_idx & (data['rt'] < med_cor)] = 'fast'
        rt_split_cor_inc[subj_idx & cor_idx & (data['rt'] >= med_cor)] = 'slow'
        rt_split_cor_inc[subj_idx & inc_idx & (data['rt'] < med_inc)] = 'fast'
        rt_split_cor_inc[subj_idx & inc_idx & (data['rt'] >= med_inc)] = 'slow'
        rt_split[subj_idx & (data['rt'] < med)] = 'fast'
        rt_split[subj_idx & (data['rt'] >= med)] = 'slow'

    conf = np.array(data['conf'] == 'HC', dtype=np.float)
    conf_effect = np.empty(data.shape, dtype=[('conf_effect',np.float)])
    conf_effect['conf_effect'] = conf

    LL = np.array(data['stim'] == 'LL', dtype=np.float)
    LL_effect = np.empty(data.shape, dtype=[('LL_effect',np.float)])
    LL_effect['LL_effect'] = LL

    WW = np.array(data['stim'] == 'WW', dtype=np.float)
    WW_effect = np.empty(data.shape, dtype=[('WW_effect',np.float)])
    WW_effect['WW_effect'] = WW


    data = rec.append_fields(data, names=('theta_split','rt_split', 'rt_split_cor_inc', 'conf_effect', 'LL_effect', 'WW_effect'),
                             data=(theta_median,rt_split,rt_split_cor_inc,conf_effect, LL_effect, WW_effect), dtypes=('S8', 'S8', 'S8', np.float, np.float, np.float), usemask=False)

    return data

def load_csv_jim(*args, **kwargs):
    if kwargs.has_key('cutoff'):
        cutoff = kwargs['cutoff']
    else:
        cutoff = .4
        
    try:
        data = np.recfromtxt(*args, dtype=[('subj_idx', '<i8'), ('stim', 'S8'), ('rt', '<f8'), ('response', '<i8'), ('theta', '<f8'), ('conf', 'S8')], delimiter=',', skip_header=True)
    except TypeError:
        data = np.recfromtxt(*args, dtype=[('subj_idx', '<i8'), ('stim', 'S8'), ('rt', '<f8'), ('response', '<i8'), ('theta', '<f8'), ('conf', 'S8')], delimiter=',', skiprows=1)

    data['stim'][data['stim'] == '1'] = 'WW'
    data['stim'][data['stim'] == '2'] = 'LL'
    data['stim'][data['stim'] == '3'] = 'WL'

    data['conf'][data['conf'] == '1'] = 'HC'
    data['conf'][data['conf'] == '2'] = 'LC'
    print data['conf'] == 'HC'

    data = add_median_fields(data)

    return data[data['rt'] > cutoff]

def set_proposals(mc, tau=.1, effect=.01, a=.5, v=.5, adaptive=False):
    for var in mc.variables:
        if var.__name__.endswith('tau'):
            # Change proposal SD
            mc.use_step_method(pm.Metropolis, var, proposal_sd = tau)
        if var.__name__.startswith('e1') or var.__name__.startswith('e2') or var.__name__.startswith('e_inter'):
            # Change proposal SD
            mc.use_step_method(pm.Metropolis, var, proposal_sd = effect)
            
        if var.__name__.startswith('a'):
            # Change proposal SD
            mc.use_step_method(pm.Metropolis, var, proposal_sd = a)
        if var.__name__.startswith('v'):
            # Change proposal SD
            mc.use_step_method(pm.Metropolis, var, proposal_sd = v)

    return

def set_adaptive_for_effects(mc, sd=.5):
    for name, child_nodes in mc._dict_container.iteritems():
        if not name.startswith('e') or name.startswith('e_inst'):
            continue

        mc.use_step_method(pm.AdaptiveMetropolis, child_nodes)

            

def create_models_corr():
    # Load data
    data_diss = load_csv_jim('DissData_P01.csv')
    data_sen =  load_csv_jim('DBSC_N15_P03.csv')
    data_easy = load_csv_jim('DBSC_N15_EASY.csv')
    data_pd = hddm.utils.load_csv('PD_PS.csv')
    data_pd = add_median_fields(data_pd)

    data_pd_dbs_off = data_pd[data_pd['dbs'] == 0]
    data_pd_dbs_on = data_pd[data_pd['dbs'] == 1]

    datasets = [data_diss, data_sen, data_easy, data_pd_dbs_off, data_pd_dbs_on]
    names = ['data_diss', 'data_sen', 'data_easy', 'data_pd_dbs_off', 'data_pd_dbs_on']
    excludes = [['T'], ['Z'], ['T','Z'], []]
    
    models = []
    
    for dataset in datasets:
        models.append({'data': dataset,
                       'effects_on':{'a': ['theta', 'conf_effect']},
                       'depends_on':{'v': 'stim'}, 
                       'model_type':'full',
                       'exclude':['T','Z']})

    return models, names


def run_model(params, name=None, load=False):
    import kabuki
    import sys
    dbname = name+'.db'

    if params.has_key('effects_on'):
        mc = pm.MCMC(hddm.model.HDDMRegressor(**params).create(), db='pickle', dbname=dbname)
    else:
        mc = pm.MCMC(hddm.model.HDDM(**params).create(), db='pickle', dbname=dbname)
    
    if not load:
        try:
            os.remove(dbname)
        except OSError:
            pass

    mc.sample(10000, burn=5000)
    mc.db.close()
    print "*************************************\n"
    kabuki.group.print_group_stats(mc.stats())
    print "DIC: %f" % mc.dic
    print "logp: %f" % mc.logp
    sys.stdout.flush()
    return mc
    
def run_correl():
    models, names = create_models_corr()
    results = {}
    for model, name in zip(models,names):
        results[name] = run_model(model, name=name)
    
    return results


def create_combined(samples=20000, burn=10000, path=None):
    datasets, names = load_datasets(path=path)

    models = []
    
    # COMBINED
    models.append({'data': datasets[-1],
                   'effects_on': {'a':['theta', 'conf_effect']}, 
                   'depends_on': {'v':['stim','group'], 'a':'group', 't':'group', 'e_theta_a':'group', 'e_conf_effect_a':'group', 'V':'group'},
                   'use_root_for_effects':True, 
                   'model_type':'full', 
                   'exclude':['Z','T'],
                   'name':'combined'})

    models.append({'data': datasets[-1],
                   'effects_on': {'a':['theta', 'conf_effect']}, 
                   'depends_on': {'v':['stim','group'], 'a':'group', 't':'group', 'e_theta_a':'group', 'e_conf_effect_a':'group', 'V':'group', 'e_inter_theta_conf_effect_a':'group'},
                   'use_root_for_effects':True,
                   'model_type':'full', 
                   'exclude':['Z','T'],
                   'name':'combined'})

    # DBS ON
    models.append({'data': datasets[-2], 
                   'effects_on': {'a':['theta', 'conf_effect']}, 
                   'depends_on': {'v':'stim'},
                   'use_root_for_effects':True, 
                   'model_type':'full', 
                   'exclude':['Z','T'],
                   'name': 'dbs_on'})

    # DBS OFF
    models.append({'data': datasets[-3], 
                   'effects_on': {'a':['theta', 'conf_effect']}, 
                   'depends_on': {'v':'stim'}, 
                   'use_root_for_effects':True, 
                   'model_type':'full', 
                   'exclude':['Z','T'],
                   'name': 'dbs_off'})
                  
    return models

if __name__=='__main__':
    import sys
    from mpi4py import MPI
    import kabuki
    rank = MPI.COMM_WORLD.Get_rank()
    if rank == 0:
        models = create_combined(path='/home/wiecki/working/projects/hddm_data/data')
        results = hddm.mpi.controller(models)
        print results
        for model,result in zip(models, results):
            print "****************************************\n"
            del model['data']
            kabuki.group.print_group_stats(result)
            sys.stdout.flush()

        #for name, model in results.iteritems():
        #    
    else:
        hddm.mpi.worker()
        