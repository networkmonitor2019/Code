from Code.Tools import get_node_deg_map
from Code.Tools import get_graph_instances
from Code.Tools import get_adjtable
from Code.Tools import pickle_to_disk
from Code.Tools import get_instances
from Code.Tools import get_ttl_dist
from Code.Tools import format_message
from Code.Tools import get_elapsed_minute

from Config import *
import os
from time import clock
import heapq


def maximize_degree_discount_heuristic(adj_table, maximal_monitor_num):
    """
    :param adj_table: {node_id: {nbor_id: weight}}
    :param maximal_monitor_num:
    :return: Choose nodes to cover as many edges as possible
    """
    
    node_deg_map = get_node_deg_map(adj_table, adj_table.iterkeys()) 

    """
    Heap in python is min-heap. We want to find nodes with largest degree.
    Thus we push neg-degree into heap.
    """
    h = []
    for node in node_deg_map:
        heapq.heappush(h, (-1 * node_deg_map[node], node))

    monitors = []

    # {node_id: degree reduction}
    node_deg_reduction_map = {}
    while True:
        neg_deg, node = heapq.heappop(h)

        """
        if node in node_deg_reduction_map, then we need to adjust the degree of node to be:
        degree = degree - node_deg_reduction_map
        We store (-1) * degree in heap. 
        Thus, (-1) * degree = (-1) * degree + node_deg_reduction_map
        """
        if node in node_deg_reduction_map:
            neg_deg += node_deg_reduction_map[node]
            del node_deg_reduction_map[node]
            heapq.heappush(h, (neg_deg, node))
            continue

        """
        if node not in node_deg_reduction_map, then we add node to monitor and 
        update the node_deg_reduction_map. 
        """
        monitors.append(node)
        if len(monitors) == maximal_monitor_num:
            break

        for nbor in adj_table[node]:
            node_deg_reduction_map[nbor] = node_deg_reduction_map.setdefault(nbor, 0) + adj_table[node][nbor]

    return monitors, get_ttl_dist(adj_table, monitors)


def do_maximize_degree_discount_heuristic_job(monitor_list, sub_pipe=None):
    """
    :param monitor_list: [..., monitor_k,...]
    :param sub_pipe:
    Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.
    :return:
    """
    related_graph_id_list = get_graph_instances(graph_dir,
                                                graph_name_str,
                                                monitor_list,
                                                monitor_pattern,
                                                sep)

    """
    monitor_pattern (reference pattern):

    [graph_name_str, monitor_info_fmt, monitor_str]

    monitor_message_pattern:
                                       ***********  ****************
    [graph_name_str, monitor_info_fmt, penalty_str, elapsed_time_str]
    """
    message_list = get_instances(monitor_pattern,
                                 monitor_msg_pattern,
                                 monitor_list,
                                 sep)

    """
    Parse parameter trunc number and trunc step
    """
    monitor_info_list = get_instances(monitor_pattern,
                                      monitor_info_str,
                                      monitor_list,
                                      sep)

    """
    [... (trunc number, trunc step) ...]
    """
    trunc_num_step_list = [parse_trunc_num_step(item) for item in monitor_info_list]

    for i in range(0, len(monitor_list)):
        graph_path = os.path.join(graph_dir, related_graph_id_list[i])
        adj_table = get_adjtable(graph_path)
        monitor_path = os.path.join(monitor_dir, monitor_list[i])

        node_num = len(adj_table)
        start_time = clock()
        monitors, penalty = maximize_degree_discount_heuristic(adj_table,
                                                               get_max_monitor_num(node_num))
        end_time = clock()

        trunc_num, trunc_step = trunc_num_step_list[i]
        monitors = [monitors[0: trunc_idx * trunc_step] for trunc_idx in range(1, trunc_num+1, 1)]
        pickle_to_disk(monitor_path, monitors)

        message_list[i] = message_list[i].replace(penalty_str, str(penalty))
        message_list[i] = message_list[i].replace(elapsed_time_str,
                                                  str(get_elapsed_minute(start_time, end_time)))
        message_list[i] = format_message(message_list[i],
                                         sep)
        print message_list[i]

    if sub_pipe:
        sub_pipe.send(message_list)
