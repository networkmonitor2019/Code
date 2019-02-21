"""
These strings are used to generate different pattern.
"""

"""
Different units are joined by sep to form pattern.
"""
sep = '__'

"""
Different strings are joined by unit_sep to form unit.
"""
unit_sep = '_'

"""
Different units
"""

"""
These units will used by all methods.

monitor_info_fmt will be instantiated as truncate-point-num_truncate-step which means that
we will truncate initial solutions at truncate-step * 1, ..., truncate-step * truncate-point-num. 
"""

graph_name_str = unit_sep.join(['graph_title', 'name'])

model_type_str = unit_sep.join(['model', 'type'])
instance_num_str = unit_sep.join(['instance', 'num'])

elapsed_time_str = unit_sep.join(['elasped', 'time'])
penalty_str = 'penalty'
monitor_str = 'monitor'
monitor_info_str = 'monitor_info'


monitor_pattern = sep.join([graph_name_str,
                            monitor_info_str,
                            monitor_str])

monitor_msg_pattern = sep.join([graph_name_str,
                                monitor_info_str,
                                penalty_str,
                                elapsed_time_str])

init_sol_str = 'init_sol'
"""
init_sol_monitor_info_str will be instantiated as max-monitor-num_method-name which means that 
we find max-monitor-num nodes as initial nodes for method-name.
"""
init_sol_monitor_info_str = 'init_sol_monitor_info'

"""
These units will be used by simulation of propagation.
"""
snapshot_str = 'snapshot'
snapshot_num_str = 'snapshot_num'

"""
These units will be used by evaluation of performance.
"""

"""
For SIR, infection_info_str will be instantiated as 
'SIR_infection_prob'_'SIR_recovery_prob'_'SIR_maximal_simu_step'_'SIR_simu_round'
For IC,  infection_info_str will be instantiated as
'IC_activation_prob'_'IC_maximal_simu_step'_'IC_simu_round'
"""
infection_info_str = 'infection_info'

snapshot_pattern = sep.join([graph_name_str,
                             infection_info_str,
                             snapshot_num_str,
                             snapshot_str])

snapshot_msg_pattern = sep.join([graph_name_str,
                                 infection_info_str,
                                 snapshot_num_str])

avg_detection_time_str = 'avg_detec_time'
detection_ratio_str = 'detection_ratio'


# This is the pattern of instances that are used to instantiate monitor_info_fmt
# Do not use trunc_num, for '_' is our unit_sep.
trunc_num_str = 'num'
step_str = 'step'
method_str = 'method'

trunc_num_step_str = unit_sep.join([trunc_num_str, step_str])
monitor_info_pattern = unit_sep.join([trunc_num_step_str, method_str])





