from Code.Tools import get_adjtable
from Code.Tools import pickle_to_disk
from Code.Tools import get_level_net
from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import format_message
from Code.Tools import get_elapsed_minute

from PatternConfig import *
from Config import *
from random import sample
from time import clock

from os import listdir


def get_roots(adj_table, root_num):
    """
    :param adj_table: {node_id:{nbor_id: weight}}
    :param root_num:
    number of roots which should be equal to the number of trees
    :return: Randomly sample a list of nodes to be the roots of trees.
    """
    return sample(adj_table.keys(), root_num)


def get_nodes_dist_to_root(level_net, nodes):
    """
    :param level_net: [...{... a:set(b,c),...}, {...b:set(d),c:set()...}, {d:set()}...]
    :param nodes: [... node_k ...]
    :return: [... dist_k ...]
    dist_k is the distance from node_k to root.
    """

    # node_dist_map = {node_id: distance from node_id to root}
    node_dist_map = {}
    dist = 0
    for level in level_net:
        for node in level.iterkeys():
            node_dist_map[node] = dist
        dist += 1

    dist_to_root = []
    for node in nodes:
        dist_to_root.append(node_dist_map[node])

    return dist_to_root


def estimate_nodes_ttl_dist(adj_table,
                            roots,
                            nodes):
    """
    :param adj_table: {node_id:{nbor_id: weight}}
    :param roots: [...,root_i,...]
    :param nodes: [...,node_j,...]
    :return: [..., estimated_total_distance_j, ...]
    estimated_total_distance_j is the estimated total distance of node_j
    """

    """
    For each node u in nodes, for each root r in roots, compute d(u,r).
    Then  [\sum_{r in roots} d(u,r)] * (node_num/root_num) as the estimated
    total distance of u to other nodes.
    """
    node_num = len(nodes)
    estimated_ttl_dist = [0] * node_num
    for root in roots:
        level_net = get_level_net(adj_table, [root])
        dist_to_root = get_nodes_dist_to_root(level_net, nodes)

        for idx in range(0, node_num):
            estimated_ttl_dist[idx] += dist_to_root[idx]

    root_num = len(roots)
    ratio = float(node_num) / root_num
    for idx in range(0, node_num):
        estimated_ttl_dist[idx] = int(estimated_ttl_dist[idx] * ratio)

    return estimated_ttl_dist


def get_node_ttl_dist_map(adj_table,
                          tree_num):
    """
    :param adj_table: {node:{nbor: weight}}
    :param tree_num: number of trees used in estimation of total distance
    :return: Write {... node_id: estimated total distance ...} directly into disk.
    """

    nodes = adj_table.keys()
    ttl_dist_list = estimate_nodes_ttl_dist(adj_table,
                                            get_roots(adj_table, tree_num),
                                            nodes)
    node_ttl_dist_map = dict(zip(nodes, ttl_dist_list))
    return node_ttl_dist_map


def do_get_node_ttl_dist_map_job(node_ttl_dist_map_list, sub_pipe=None):
    """
    :param node_ttl_dist_map_list: [... node_ttl_dist_map_k ...]
    :param sub_pipe: Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.
    :return:
    """
    """
    node_ttl_dist_map_pattern(reference pattern):
                     
    [graph_name_str, tree_method_info_str, node_ttl_dist_map_str]
    tree_method_info : 'tree num'_'tree method'
    
    """

    """
    Instantiate node_ttl_dist_map_msg_pattern:
                                      
    [graph_name_str, tree_method_info_str, elapsed_time_str]
    """
    msg_list = get_instances(node_ttl_dist_map_pattern,
                             node_ttl_dist_map_msg_pattern,
                             node_ttl_dist_map_list,
                             sep)
    msg_to_send = []


    """
    Parse parameter tree_num
    """
    tree_method_info_list = get_instances(node_ttl_dist_map_pattern,
                                          tree_method_info_str,
                                          node_ttl_dist_map_list,
                                          sep)
    tree_num_list = [parse_tree_num(item) for item in tree_method_info_list]

    related_graph_list = get_graph_instances(graph_dir,
                                             graph_name_str,
                                             node_ttl_dist_map_list,
                                             node_ttl_dist_map_pattern,
                                             sep
                                             )

    for i in range(0, len(node_ttl_dist_map_list)):
        graph_path = path.join(graph_dir, related_graph_list[i])
        adj_table = get_adjtable(graph_path)

        node_ttl_dist_map_path = path.join(node_ttl_dist_map_dir, node_ttl_dist_map_list[i])

        start_time = clock()
        node_ttl_dist_map = get_node_ttl_dist_map(adj_table, tree_num_list[i])
        end_time = clock()

        pickle_to_disk(node_ttl_dist_map_path, node_ttl_dist_map)

        """
        Instantiate elapsed_time_str in node_ttl_dist_map_msg_pattern.
        """
        msg_list[i] = msg_list[i].replace(elapsed_time_str, str(get_elapsed_minute(start_time,
                                                                end_time)))

        msg_list[i] = format_message(msg_list[i], sep)
        print msg_list[i]
        msg_to_send.append(msg_list[i])

    if sub_pipe:
        sub_pipe.send(msg_to_send)

















