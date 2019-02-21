from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep

model_list = ['RE_0.02_10000', '3.0_2_50000']
instance_num_range = range(0, 10)

methods = ['local_search', 'CSAV++', 'clc', 'deg']

penalty_dir = path.join(general_dir, 'penalty')
create_dir(penalty_dir)
penalty_log_path = path.join(general_dir, 'penalty_log.txt')

trunc_num_step_fmt = unit_sep.join(['{0:d}', '{1:d}'])
monitor_info_fmt = unit_sep.join(['{0:s}', '{1:s}'])


def get_scale_from_model_type(model):
    return int(model[model.rfind('_') + 1:])

