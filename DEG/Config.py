from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import *

graph_id_list = listdir(graph_dir)

method_name = 'DEG'

trunc_num_step_method = unit_sep.join(['{0:d}', '{1:d}', method_name])


def parse_trunc_num_step(instance):
    """
    :param instance: An instantiation of '{0:d}_{1:d}_DEG'
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










