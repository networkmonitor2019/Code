import heapq

from Code.Tools import get_adjtable
from Code.Tools import get_ttl_dist
from Code.Tools import pickle_to_disk
from Code.Tools import pickle_from_disk
from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import format_message
from Code.Tools import get_elapsed_minute
from ImproveInitSol import get_random_lev_net

from Config import *
from PatternConfig import *
from ImproveInitSol import fast_get_ttl_dist
from ImproveInitSol import get_candidates
from ImproveInitSol import get_node_root_dist_map

from time import clock
from os import listdir


def get_init_sol(adj_table,
                 node_ttl_dist_map,
                 max_monitor_num):
    """
    :param adj_table: {node_id: {nbor_id: weight}}

    :param node_ttl_dist_map: path of node_ttl_dist_map
    {node_id: total distance from node_id to other nodes}

    :param max_monitor_num:

    :return: initial solution
    """
    node_num = len(adj_table)
    candidate_num = get_init_sol_candidate_num(node_num)

    """
    penalty(M) is total distance from M to other nodes
    when M = \empty, penalty is |V|^2
    """
    penalty_of_empty = node_num ** 2

    """
    The candidates for the first node is the k = candidate_num nodes with largest marginal reward
    for a node u, delta(u) = R(u) - R(empty) = penalty(empty)-penalty(u)
    Thus, it is equivalent to find k nodes with smallest penalty.
    """
    candidates = heapq.nsmallest(candidate_num,
                                 node_ttl_dist_map,
                                 node_ttl_dist_map.get)

    # heap to store the negative of marginal reward
    h = []
    # the marginal reward of u is updated <=> u in updated.
    updated = {}

    """
    a tried node u means that u has been updated at least once.
    u in the heap or u chosen as a monitor <=> u in tried_nodes
    """
    tried_nodes = {}

    """
    Assume we have chosen set M, in next chosen_monitor_num, 
    we need to choose u, such that delta(u) = R({u} \union M) - R(M) is maximized.
    Thus we store -1 * delta(u) = penalty({u} \union M) - penalty(M)
    in the min-heap of python.
    We adopt the lazy-forward updating.
    """
    """
    Initialize heap. M = \empty
    """
    for node in candidates:
        heapq.heappush(h, (get_ttl_dist(adj_table, [node]) - penalty_of_empty, node))
        updated[node] = None
        tried_nodes[node] = None

    monitors = []
    penalty = penalty_of_empty

    while h:
        neg_delta, node = heapq.heappop(h)

        """
        IF the node hasn't been updated, update it and put back.
        ELSE the node has the largest marginal reward.
        """
        if node not in updated:
            # neg_delta = get_ttl_dist(adj_table, monitors + [node]) - penalty
            neg_delta = fast_get_ttl_dist(adj_table,
                                          node_root_dist_map,
                                          penalty,
                                          [node]) - penalty

            heapq.heappush(h, (neg_delta, node))
            updated[node] = None
            continue

        """
        Put the node in monitors 
        penalty(M\union {u}) = penalty(M) - delta
        """
        monitors.append(node)
        penalty += neg_delta
        if len(monitors) == max_monitor_num:
            break

        """
        Generate new candidates for chosen monitors.
        Note that: u in tried_nodes <=> u is in the heap or chosen as a verify_monitor
        in either case, we do not need to calculate marginal reward and put into
        the heap. 
        """
        updated = {}

        level_net = get_random_lev_net(adj_table, monitors, seed=1)

        candidates = get_candidates(adj_table, level_net, candidate_num)
        node_root_dist_map = get_node_root_dist_map(level_net)

        for candidate in candidates:
            if candidate in tried_nodes:
                continue
            neg_delta = fast_get_ttl_dist(adj_table,
                                          node_root_dist_map,
                                          penalty,
                                          [candidate]) - penalty

            heapq.heappush(h, (neg_delta, candidate))
            updated[candidate] = None
            tried_nodes[candidate] = None

    return monitors, penalty


def do_get_init_sol_job(init_sol_list, sub_pipe=None):
    """
    :param init_sol_list: [..., init_sol_k, ...]
    :param sub_pipe: Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.
    """
    """
    init_sol_pattern(reference pattern):                   
    [graph_name_str, tree_method_info_str, init_sol_monitor_info_str, init_sol_str]
    tree_method_info : tree-num_tree-method
    init_sol_monitor_info: max-monitor-num_method
    """

    """
    Instantiate node_ttl_dist_map_pattern.
    node_ttl_dist_map_pattern:                                            
    [graph_name_str, tree_method_info_str, node_ttl_dist_map_str]
                           
    """
    node_ttl_dist_map_list = get_instances(init_sol_pattern,
                                           node_ttl_dist_map_pattern,
                                           init_sol_list,
                                           sep
                                           )

    """
    Instantiate init_sol_message_pattern. 
    init_sol_message_pattern: 
    [graph_name_str, tree_method_info_str, init_sol_monitor_info_str, 
    ***********  ****************
    penalty_str, elapsed_time_str]   

    """
    msg_list = get_instances(init_sol_pattern,
                             init_sol_msg_pattern,
                             init_sol_list,
                             sep)

    msg_to_send = []

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
                                                init_sol_pattern,
                                                sep)

    for i in range(0, len(init_sol_list)):

        """
        Load adjacent table. 
        """
        graph_path = path.join(graph_dir, related_graph_id_list[i])
        adj_table = get_adjtable(graph_path)

        """
        Load node_ttl_dist_map.
        """
        node_ttl_dist_map_path = path.join(node_ttl_dist_map_dir, node_ttl_dist_map_list[i])
        node_ttl_dist_map = pickle_from_disk(node_ttl_dist_map_path)

        """
        Get initial solution and write to disk.
        """
        init_sol_path = path.join(init_sol_dir, init_sol_list[i])
        start_time = clock()
        monitors, penalty = get_init_sol(adj_table, node_ttl_dist_map, max_monitor_num_list[i])
        end_time = clock()
        pickle_to_disk(init_sol_path, monitors)

        """
        Instantiate penalty_str and elapsed_time_str in init_sol_message_pattern.
        """
        msg_list[i] = msg_list[i].replace(penalty_str, str(penalty))
        msg_list[i] = msg_list[i].replace(elapsed_time_str,
                                          str(get_elapsed_minute(start_time, end_time)))

        """
        Process msg.
        """
        msg_list[i] = format_message(msg_list[i], sep)
        print msg_list[i]
        msg_to_send.append(msg_list[i])

    if sub_pipe:
        sub_pipe.send(msg_to_send)


