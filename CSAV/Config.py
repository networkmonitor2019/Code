from Code.GeneralConfig.Config import *
from Code.GeneralConfig.PatternConfig import unit_sep
from math import log
from math import ceil
from Code.Tools import create_dir

graph_id_list = listdir(graph_dir)

# In a step of improvement, if the reward <= stop_criteria, then we stop.
stop_criteria = 0

tree_method_name = 'rand'
method_name = 'CSAV++'


"""
In tree_num_method, '{0:d}' can be instantiated as the number of trees used to estimate total distance.
In max_monitor_num_method, '{0:d}' can be instantiated as the max monitor number.
In monitor_info_fmt, '{0:d}-{1:d}' can be instantiated as truncate_point_num-step
The initial solution will truncated at step * 1, step * 2, ...., step * truncate_point_num locations.
"""
tree_num_method = unit_sep.join(['{0:d}', tree_method_name])


def parse_tree_num(instance):
    """
    :param instance: An instantiation of '{0:d}_rand'
    :return:
    """
    end_idx = instance.find(unit_sep)
    return int(instance[0:end_idx])


max_monitor_num_method = unit_sep.join(['{0:d}', method_name])


def parse_max_monitor_num(instance):
    """
    :param instance: An instantiation of '{0:d}_CSAV'
    :return:
    """
    end_idx = instance.find(unit_sep)
    return int(instance[0:end_idx])


trunc_num_step_method = unit_sep.join(['{0:d}', '{1:d}', method_name])


def parse_trunc_num_step(instance):
    """
    :param instance: An instantiation of '{0:d}_{1:d}_CSAV'
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


node_ttl_dist_map_dir = path.join(general_dir, 'node_ttl_dist_map')
create_dir(node_ttl_dist_map_dir)
node_ttl_dist_map_log_path = path.join(general_dir, 'node_ttl_dist_map_log')

init_sol_dir = path.join(general_dir, method_name + '_init_sol')
create_dir(init_sol_dir)
init_sol_log_path = path.join(general_dir, method_name + '_init_sol_record')


def get_tree_num(node_num):
    """
    :param node_num: node number of the graph_title
    :return: number of trees used to approximate total distance.
    """
    # return (int(log(node_num, 2)) + 1) ** 2
    return int(ceil(log(node_num, 2))) ** 2


"""
To improve the initial solution, we at most repeat maximal_iter_step steps.
In each step, we search along each component with other components fixed. The candidate num of searching
each component is returned by 'get_improvement_candidate_num'.
"""


def get_init_sol_candidate_num(node_num):
    """
    :param node_num: node num of the network
    :param maximal_monitor_num:
    :return:
    """
    return get_max_monitor_num(node_num)


def get_improvement_maximal_iter_step(node_num):
    """
    :param node_num:
    :return:
    """
    return int(log(node_num, 2)) ** 2


def get_improvement_candidate_num(node_num):
    """
    :param node_num:
    :return: search space size of improvement stage
    """
    return int(log(node_num, 2)) ** 2



