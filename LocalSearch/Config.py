from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep
from Code.Tools import create_dir

graph_id_list = listdir(graph_dir)

# After a step of improvement, if the reward <= stop_criteria, then we stop.
stop_criteria = 0

method_name = 'LS'


max_monitor_num_method = unit_sep.join(['{0:d}', method_name])


def parse_max_monitor_num(instance):
    """
    :param instance: an instantiation of '{0:d}_LS'
    :return:
    """
    end_idx = instance.find(unit_sep)
    return int(instance[0:end_idx])


trunc_num_step_method = unit_sep.join(['{0:d}', '{1:d}', method_name])


def parse_trunc_num_step(instance):
    """
    :param instance: an instantiation of '{0:d}_{1:d}_LS'
    :return:
    """
    start = instance.find(unit_sep)
    trunc_num = int(instance[0:start])
    """
    Do not forget to skip the unit_sep itself.
    """
    start += 1

    end = instance.find(unit_sep, start)
    step = int(instance[start:end])
    return trunc_num, step


init_sol_dir = path.join(general_dir, method_name + '_init_sol')
create_dir(init_sol_dir)
init_sol_log_path = path.join(general_dir, method_name + '_init_sol_record')







