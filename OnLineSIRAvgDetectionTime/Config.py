from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep

graph_id_list = listdir(graph_dir)  # graph_id : graph_name__type

methods = ['LS', 'CSAV++', 'clc', 'deg']

trunc_num_step_fmt = unit_sep.join(['{0:d}', '{1:d}'])
monitor_info_fmt = unit_sep.join(['{0:s}', '{1:s}'])

avg_detection_time_dir = path.join(general_dir, 'avg_detection_time')
create_dir(avg_detection_time_dir)

avg_detection_time_log_path = path.join(general_dir, 'SIR_avg_detection_time_record.txt')


"""
We do not need to set maximal step any more.
"""
infection_prob = 0.6
recovery_prob = 0.2
infection_info_instant = (unit_sep.join(['{0:.2f}', '{1:.2f}'])).format(
    infection_prob,
    recovery_prob
)

"""
We need snapshot_num snapshots
"""
snapshot_num = 10000

"""
We accept a snapshot <=> |{u: u has been infected}|/|V| > infection ratio
"""
infection_ratio = 0.0
"""
If the infection ratio is lower than 'infection_ratio' after 'alert_round', then stop
and alert.
"""
alert_round = 1000


