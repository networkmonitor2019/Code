from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep

graph_id_list = listdir(graph_dir)
methods = ['LS', 'CSAV++', 'clc', 'deg']

penalty_dir = path.join(general_dir, 'penalty')
create_dir(penalty_dir)
penalty_log_path = path.join(general_dir, 'penalty_log.txt')

trunc_num_step_fmt = unit_sep.join(['{0:d}', '{1:d}'])
monitor_info_fmt = unit_sep.join(['{0:s}', '{1:s}'])
