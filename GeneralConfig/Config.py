from Code.Tools import create_dir
from os import path
from os import listdir
from math import log
from math import ceil

# Everything is under this directory
general_dir = '../../Test_Data'

# graph_title directory
graph_dir = path.join(general_dir, 'graph')
create_dir(graph_dir)

# graph_title scale log is used to store the graph_name, node number, edge number
graph_scale_log_path = path.join(general_dir, 'graph_scale_log')

# monitor directory
monitor_dir = path.join(general_dir, 'monitor')
create_dir(monitor_dir)
monitor_log_path = path.join(general_dir, 'monitor_log')

"""
Given initial solution s = [s_0, ..., s_{maximal_monitor_num-1}] and max_trunc_num
then s_0, ..., s_{max_trunc_num - 1} is the segment which we can truncate. 
We truncate it as 
s[0: 1*trunc_step], s[0: 2*trunc_step], ..., s[0: trunc_point_num*trunc_step], where 
trunc_step = max_trunc_num / trunc_point_num. Make sure that trunc_step > 0.
"""
trunc_point_num = 1


def get_step(max_monitor_num):
    """
    :param max_monitor_num: max number of points that can be truncated.
    :return: step
    """
    step = max_monitor_num / trunc_point_num
    return step


def get_max_monitor_num(node_num):
    """
    :param node_num:
    :return:
    """
    k = int(ceil(log(node_num, 2))) ** 2
    base = 1
    while True:
        if 1 <= k/base < 10:
            break
        base *= 10

    return int(ceil(float(k)/base)) * base


accessible_cpu_num = 4






