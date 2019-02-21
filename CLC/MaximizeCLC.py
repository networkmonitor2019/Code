from Code.Tools import get_adjtable
from Code.Tools import pickle_to_disk
from Code.Tools import get_graph_instances
from Code.Tools import get_instances
from Code.Tools import format_message
from Code.Tools import get_ttl_dist
from Code.Tools import get_elapsed_minute

from Config import *
import os
from time import clock
"""
C_{LC}(V) = \sum_{u \in Nbor(V)} weight(u)

where weight(u) = \sum_{w \in Nbor(u)} N(w),

where N(w) is the number of nodes that are available for u  within 2 steps.
"""


def get_node_weight_map(adj_table):
    """
    :param adj_table: {node_id:{nbor_id: weight, ...}, ...}
    :return: {node_id: weight}
    """
    """
    For each node v, we first compute number of nodes that are available for u 
    within 2 steps. 
    """
    node_nbor_size_map = {}
    for v in adj_table:
        nbor = set(adj_table[v].iterkeys())
        for u in adj_table[v].iterkeys():
            for w in adj_table[u].iterkeys():
                nbor.add(w)
        node_nbor_size_map[v] = len(nbor)

    """
    For each node v, we compute its weight. weight(v) = \sum_{u \in Nbor(v)} N(u)
    where N(u) is the number of nodes that are available for u within 2 steps. 
    """
    node_weight_map = {}
    for v in adj_table:
        node_weight_map[v] = 0
        for u in adj_table[v]:
            node_weight_map[v] += node_nbor_size_map[u]

    return node_weight_map


def get_marginal_reward(adj_table, u, nbors, node_weight_map):
    """
    :param adj_table: {node:{nbor: degree ...} ...}
    :param u: a node
    :param nbors: a neighborhood set.
    :param node_weight_map: {node: weight}
    :return: marginal reward of adding
    marginal reward of adding u: summation of the weight of new neighbors of u.
    new neighbors of u: {x: x is neighbor of u and x not in nbors}
    """
    marginal_reward = 0
    for v in set(adj_table[u].iterkeys()).difference(nbors):
        marginal_reward += node_weight_map[v]

    return marginal_reward


def maximize_comb_local_centrality(adj_table, maximal_monitor_num):
    """
    :param adj_table: {node:{nbor:weight}}
    :param maximal_monitor_num:
    :return: Find maximal_monitor_num nodes to maximize the combinatorial local centrality,
    and write the result into central_node_path
    """

    """
    node_weight_map = {node: weight}
    For u, weight(u) = \sum_{w \in Nbor(u)} N(w)
    """
    node_weight_map = get_node_weight_map(adj_table)

    # nodes that maximize the combinatorial local centrality
    central_nodes = []
    # neighbors of the chosen nodes
    nbors = set([])

    node_marginal_reward_map = dict(zip(adj_table.iterkeys(), [float('inf')] * len(adj_table)))

    while True:
        if len(central_nodes) == maximal_monitor_num:
            break

        marginal_reward = 0
        chosen_node = None
        for node in node_marginal_reward_map:

            if node_marginal_reward_map[node] > marginal_reward:
                tmp_marginal_reward = get_marginal_reward(adj_table,
                                                          node,
                                                          nbors,
                                                          node_weight_map)

                node_marginal_reward_map[node] = tmp_marginal_reward

                if tmp_marginal_reward > marginal_reward:
                    marginal_reward = tmp_marginal_reward
                    chosen_node = node

        if marginal_reward == 0:
            break

        del node_marginal_reward_map[chosen_node]
        central_nodes.append(chosen_node)
        nbors.update(adj_table[chosen_node].iterkeys())
    return central_nodes, get_ttl_dist(adj_table, central_nodes)


def do_maximize_comb_local_centrality_job(monitor_list, sub_pipe):
    """
    :param monitor_list: [..., monitor_id,...]
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
    msg_list = get_instances(monitor_pattern,
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

        maximal_monitor_num = get_max_monitor_num(len(adj_table))

        start_time = clock()
        monitors, penalty = maximize_comb_local_centrality(adj_table, maximal_monitor_num)
        end_time = clock()

        trunc_num, trunc_step = trunc_num_step_list[i]
        monitors = [monitors[0: trunc_idx * trunc_step] for trunc_idx in range(1, trunc_num+1, 1)]

        pickle_to_disk(monitor_path, monitors)

        msg_list[i] = msg_list[i].replace(penalty_str, str(penalty))
        msg_list[i] = msg_list[i].replace(elapsed_time_str,
                                          str(get_elapsed_minute(start_time, end_time)))
        msg_list[i] = format_message(msg_list[i], sep)

        print msg_list[i]

    if sub_pipe:
        sub_pipe.send(msg_list)

