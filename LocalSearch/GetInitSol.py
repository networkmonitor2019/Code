from Code.Tools import get_ttl_dist
from Code.Tools import get_level_net
from Code.Tools import get_graph_instances
from Code.Tools import get_instances
from Code.Tools import get_adjtable
from Code.Tools import pickle_to_disk
from Code.Tools import format_message
from Code.Tools import get_elapsed_minute

from Config import *
from PatternConfig import *

import heapq
import os
from time import clock

from ImproveInitSol import fast_get_ttl_dist
from ImproveInitSol import get_node_root_dist_map


def maximize_reward(adj_table, maximal_monitor_num):
    """
    :param adj_table: {node:{nbor: weight}}
    :param maximal_monitor_num:
    :return: N, penalty of N
    where N is a node list chosen greedily to maximize reward and |N| <= maximal_monitor_num,
    penalty(N) = \sum_{v} d(v,N)
    """

    node_num = len(adj_table)
    penalty_of_empty = node_num ** 2

    h = []
    updated = {}
    """
    marginal reward of v = R({v}) - R(empty) = |V|^2 - Penalty({v})
    The heap in python is a min-heap. We want to find the node with maximal marginal reward,
    thus we store the negative of marginal reward into the heap.
    """
    for node in adj_table.iterkeys():
        heapq.heappush(h, (get_ttl_dist(adj_table, [node]) - penalty_of_empty, node))
        updated[node] = None

    # Choose maximal_monitor_num nodes
    monitors = []
    penalty = penalty_of_empty
    while h:
        neg_reward, node = heapq.heappop(h)

        """
        If node is not updated, we update it and put it back to the heap.
        If node is updated, due to the sub-modular property, we won't need to 
        update other nodes.
        """
        if node not in updated:
            neg_reward = fast_get_ttl_dist(adj_table,
                                           node_root_dist_map,
                                           penalty,
                                           [node]) - penalty
            heapq.heappush(h, (neg_reward, node))
            updated[node] = None
            continue

        monitors.append(node)
        """
        neg_reward = R(X) - R(X \union {v}) 
                   = Penalty(X \union {v}) - Penalty(X)
        Penalty(X \union {v}) = Penalty(X) + neg_reward
        """
        penalty += neg_reward
        if len(monitors) == maximal_monitor_num:
            break

        """
        Prepare data structure for fast_get_ttl_dist
        """
        level_net = get_level_net(adj_table, monitors)

        node_root_dist_map = get_node_root_dist_map(level_net)

        updated = {}

    return monitors, penalty


def do_maximize_reward_job(init_sol_list, sub_pipe=None):
    """
    :param init_sol_list: [..., init_sol_k,...]
    :param sub_pipe:
    Corresponding to a master pipe owned by the master process,
    if sub_pipe is not None, we put some information into it and send to the master pipe.
    :return:
    """

    """
    initial solution pattern (reference pattern):
    [graph_name_str, init_sol_monitor_info_str, init_sol_str]
    
    message id pattern: 
                                                ***********  ****************
    [graph_name_str, init_sol_monitor_info_str, penalty_str, elapsed_time_str]
    """
    message_id_list = get_instances(monitor_pattern,
                                    monitor_msg_pattern,
                                    init_sol_list,
                                    sep)

    """
    Parse parameter max_monitor_num.
    """
    init_sol_monitor_info_list = get_instances(init_sol_pattern,
                                               init_sol_monitor_info_str,
                                               init_sol_list,
                                               sep)

    max_monitor_num_list = [parse_max_monitor_num(item) for item in init_sol_monitor_info_list]

    related_graph_id_list = get_graph_instances(graph_dir,
                                                graph_name_str,
                                                init_sol_list,
                                                monitor_pattern,
                                                sep)

    for i in range(0, len(init_sol_list)):
        graph_path = os.path.join(graph_dir, related_graph_id_list[i])
        init_sol_path = os.path.join(init_sol_dir, init_sol_list[i])

        start_time = clock()
        init_sol, penalty = maximize_reward(get_adjtable(graph_path), max_monitor_num_list[i])
        end_time = clock()

        pickle_to_disk(init_sol_path, init_sol)

        message_id_list[i] = message_id_list[i].replace(penalty_str, str(penalty))
        message_id_list[i] = message_id_list[i].replace(elapsed_time_str,
                                                        str(get_elapsed_minute(start_time, end_time)))

        message_id_list[i] = format_message(message_id_list[i], sep)
        print message_id_list[i]

    if sub_pipe:
        sub_pipe.send(message_id_list)








