from Code.Tools import get_adjtable
from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk
from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import format_message
from Code.Tools import get_level_net
from Code.Tools import get_ttl_dist
from Code.Tools import get_elapsed_minute

from Config import *
from PatternConfig import *
import os
from time import clock


def fast_get_ttl_dist(adj_table,
                      node_root_dist_map,
                      ttl_dist,
                      nodes_to_add
                      ):
    """
    :param adj_table: {node: {nbor: weight}}

    We have a root set R, and we have a set A to add into R.
    We want to get the ttl dist from (R \cup A) to other nodes.
    We store the distance from any other node to U in node_root_dist_map.
    The whole process likes a bidirection search from A and R.
    :param node_root_dist_map: {node: dist to R}.
    :param ttl_dist: total distance from R to other nodes.
    :param nodes_to_add: [... node_k ...]
    :return: total distance from (R \cup A) to other nodes
    """

    visited = set()
    current_level = nodes_to_add

    """
    For each node u, if it satisfies dist(A, u) < dist(R, u), then we store it
    in dist_map as dist_map[u] = dist(A, u)
    """
    dist_map = {}

    dist = 0
    while current_level:
        """
        For u, if dist(A, u) >= dist(R, u). Then for any node v in the BFS subtree
        rooted at u(included u itself). 
        We have dist(A, v) = dist(A, u) + dist(u, v) >= dist(R, u) + dist(u, v) 
        >= dist(R, v)
        dist((R \cup A), v) = min{ dist(R, v), dist(A, v) } = dist(R, v).
        Thus, for any node v in the whole subtree rooted at u, 
        we do not need to visit it to get dist(A, v). 
        """
        remained_nodes = []
        for u in current_level:
            visited.add(u)
            if dist < node_root_dist_map[u]:
                remained_nodes.append(u)
                dist_map[u] = dist

        next_level = set()
        for u in remained_nodes:
            for v in adj_table[u]:
                if v not in visited and v not in next_level:
                    next_level.add(v)

        current_level = next_level
        dist += 1

    dist_decrement = 0
    for u in dist_map:
        dist_decrement += (node_root_dist_map[u] - dist_map[u])

    return ttl_dist - dist_decrement


def get_node_root_dist_map(level_net):
    """
    :param level_net:
    [{a:set(b,c),.. }, {b:set(d),c:set()}, {d:set()}]
    :return: {node: dist from node to root}
    """
    node_root_dist_map = {}
    dist = 0
    for level in level_net:
        for node in level.iterkeys():
            node_root_dist_map[node] = dist
        dist += 1

    return node_root_dist_map


def get_coordinate_improvement(adj_table,
                               monitors,
                               ttl_dist,
                               idx):
    """
    :param adj_table: {node_id: {nbor_id: weight}, ...}

    :param monitors: [..., monitor_k, ...]

    :param ttl_dist: total distance of monitors

    :param idx:

    :return: new penalty(total distance).
    [monitor_1, ..., monitor_(idx-1), u, monitor_(idx+1), ...]
    We generate candidates_num candidates for u. And choose the best one.
    """
    # Generate candidates for u
    fixed_monitors = monitors[0:idx] + monitors[idx + 1:]
    candidates = set(adj_table.iterkeys()) - set(fixed_monitors)

    level_net = get_level_net(adj_table, fixed_monitors)
    node_root_dist_map = get_node_root_dist_map(level_net)
    fixed_monitors_ttl_dist = sum(node_root_dist_map.itervalues())

    # Find a candidate that can improve the result
    for candidate in candidates:
        tmp_ttl_dist = fast_get_ttl_dist(adj_table,
                                         node_root_dist_map,
                                         fixed_monitors_ttl_dist,
                                         [candidate])
        if ttl_dist > tmp_ttl_dist:
            ttl_dist = tmp_ttl_dist
            monitors[idx] = candidate
            break

    return ttl_dist


def improve_init_sol(adj_table, init_sol):
    """
    :param adj_table: {node_id: {nbor_id: weight}}

    :param init_sol:  [..., node_k, ...]

    :return: Total dist of the improved solution. Note we will modify the init_sol in place.
    """

    ttl_dist = get_ttl_dist(adj_table, init_sol)
    last_update_idx = None

    while True:
        variation = 0
        for idx in range(0, len(init_sol)):
            new_ttl_dist = get_coordinate_improvement(adj_table,
                                                      init_sol,
                                                      ttl_dist,
                                                      idx)

            """
            get_coordinate_improvement only find a candidate to 
            improve, not the best candidate. Thus, if idx == last_update_idx,
            we also need to check whether there is an improvement at idx.
            """
            if new_ttl_dist < ttl_dist:
                last_update_idx = idx
            elif new_ttl_dist == ttl_dist and idx == last_update_idx:
                break

            variation += (ttl_dist - new_ttl_dist)
            ttl_dist = new_ttl_dist

        # print 'step: ' + str(step) + ' \t variation: ' + str(variation)
        if variation == 0:
            break

    return ttl_dist


def improve_init_sols(adj_table,
                      init_sol,
                      trunc_num,
                      trunc_step
                      ):
    """
    :param adj_table: {node_id: {nbor_id: weight}}

    :param init_sol: [..., node_k, ...]

    :param trunc_num:
    :param trunc_step:
    We will generate truncate points as [trunc_step * 1, ..., trunc_step * trunc_num]

    :return: A list of list [..., sol_m, ...],
    where sol_m corresponds to init_sol[0:m], to monitor_path.
    And the penalty of the last solution in the list.
    """
    monitors = []
    ttl_dist = None

    trunc_idx = 1
    while trunc_idx <= trunc_num:
        """
        Note that in func improve_random_init_sol, we will modify sol
        in place. Thus the shallow copy is very important.
        """
        sol = init_sol[0:trunc_idx * trunc_step]
        ttl_dist = improve_init_sol(adj_table,
                                    sol)

        monitors.append(sol)
        trunc_idx += 1

    return monitors, ttl_dist


def do_improve_init_sols_job(monitor_list, sub_pipe):
    """
    :param monitor_list: [..., monitor_id,...]
    :param sub_pipe: Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.
    :return:
    """

    """
    monitor_pattern (reference pattern):
                                                         
    [graph_name_str, monitor_info_fmt, monitor_str]
    
    init_sol_pattern:      
                     *************************                                      
    [graph_name_str, init_sol_monitor_info_str, init_sol_str]
    
    monitor_message_pattern:
                                       ***********  ****************
    [graph_name_str, monitor_info_fmt, penalty_str, elapsed_time_str]
    """

    init_sol_list = get_instances(monitor_pattern,
                                  init_sol_pattern,
                                  monitor_list,
                                  sep)

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

    related_graph_id_list = get_graph_instances(graph_dir,
                                                graph_name_str,
                                                monitor_list,
                                                monitor_pattern,
                                                sep)

    for i in range(0, len(monitor_list)):
        graph_path = os.path.join(graph_dir, related_graph_id_list[i])
        adj_table = get_adjtable(graph_path)
        node_num = len(adj_table)

        max_monitor_num = get_max_monitor_num(node_num)
        init_sol_list[i] = init_sol_list[i].replace(init_sol_monitor_info_str,
                                                    max_monitor_num_method.format(max_monitor_num))
        init_sol_path = os.path.join(init_sol_dir, init_sol_list[i])

        monitor_path = os.path.join(monitor_dir, monitor_list[i])

        init_sol = pickle_from_disk(init_sol_path)
        start_time = clock()
        monitors, penalty = improve_init_sols(adj_table, init_sol, *trunc_num_step_list[i])
        end_time = clock()

        pickle_to_disk(monitor_path, monitors)

        msg_list[i] = msg_list[i].replace(penalty_str, str(penalty))
        msg_list[i] = msg_list[i].replace(elapsed_time_str,
                                          str(get_elapsed_minute(start_time, end_time)))
        msg_list[i] = format_message(msg_list[i], sep)
        print msg_list[i]

    if sub_pipe:
        sub_pipe.send(msg_list)


