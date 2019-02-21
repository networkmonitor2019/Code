from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep

model_list = ['3.0_2_50000', '4.0_2_10000']
instance_num_range = range(1, 5)

methods = ['clc', 'deg']

trunc_num_step_fmt = unit_sep.join(['{0:d}', '{1:d}'])
monitor_info_fmt = unit_sep.join(['{0:s}', '{1:s}'])

"""
Note the source is infected in step 0.
We simulate the process step 0, 1, 2, ..., maximal_simu_step.
"""
activation_prob = 0.6
infection_info_instant = '{0:.2f}'.format(activation_prob)

avg_detection_time_dir = path.join(general_dir, 'avg_detection_time')
create_dir(avg_detection_time_dir)

if activation_prob < 1.0:
    avg_detection_time_log_path = path.join(general_dir, 'IC_avg_detection_time_record.txt')
elif activation_prob == 1.0:
    avg_detection_time_log_path = path.join(general_dir, 'FF_avg_detection_time_record.txt')


"""
We need snapshot_num snapshots
"""
snapshot_num = 100

"""
We accept a snapshot <=> |{u: u has been infected}|/|V| > infection ratio
"""
infection_ratio = 0.00
"""
If the infection ratio is lower than 'infection_ratio' after 'alert_round', then stop
and alert.
"""
alert_round = 1000


def get_scale_from_model_type(model):
    return int(model[model.rfind('_') + 1:])