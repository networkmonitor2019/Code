import heapq

from Code.Tools import get_adjtable
from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk
from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import format_message
from Code.Tools import get_ttl_dist
from Code.Tools import get_elapsed_minute



from PatternConfig import *
from Config import *

import os
import random as rd
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


def get_random_lev_net(adj_table, roots, seed):
    """
    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :param roots: an iterable object
    :param seed:
    :return: a random level network from roots by BFS
    # Example: [{a:set(b,c),.. }, {b:set(d),c:set()}, {d:set()}]
    # from left to right, it is level 0, 1, 2, .....
    """
    rd.seed(seed)
    cur_lev = list(roots)
    visited = set()
    lev_net = []

    while cur_lev:
        cur_lev = rd.sample(cur_lev, len(cur_lev))

        lev = {}
        for u in cur_lev:
            visited.add(u)
            lev[u] = []

        nxt_lev = set()
        for u in cur_lev:
            for v in adj_table[u]:
                if v not in visited and v not in nxt_lev:
                    lev[u].append(v)
                    nxt_lev.add(v)

        lev_net.append(lev)
        cur_lev = list(nxt_lev)
    return lev_net


def get_candidates(adj_table,
                   lev_net,
                   candidate_num):
    """
    :param adj_table: {node_id: {nbor_id: weight}, ...}

    :param lev_net: [{a:set(b,c),.. }, {b:set(d),c:set()}, {d:set()}]

    :param candidate_num:
    number of candidates

    :return: list of candidates
    """

    level_num = len(lev_net)

    """
    We append an empty dictionary just for convenience.
    Remember to pop it at the end of this function.
    """
    lev_net.append({})

    # {node_id: m} m is the size of subtree rooted at node_id
    node_subtree_size_map = {}
    h = []

    """
    Let R be the roots of the lev_net.
    For each u u, let l_u(the level of u) be the d(u, R).
    For each u u, let T_u be the subtree on the level network.
    For each u u, let C_u = {w: d(w, u) < d(w, R)}.
    For each u u, let N_u be the neighbor of u in the graph_title.

    Given a u x, the marginal reward of monitoring x is:
    \sum_{u \in C_x} (d(u, R) - d(u, x))

    To give a lower bound of marginal reward:
    N_x can be partitioned into three classes:
    c-1 = {u \in N_x: l_u = l_x - 1} 
    c-2 = {u \in N_x: l_u = l_x}
    c-3 = {u \in N_x: l_u = l_x + 1}

    For each u \in c-3, T_u \subset C_u. \sum_{u \in c-3} \sum_{w \in T_u} (d(w, R)-d(w, x)) 
    = \sum_{u \in c-3} \sum_{w \in T_u} (l_x) = \sum_{u \in c-3} |T_u| (l_x) 

    For each u \in c-2, if l_x > 1, then \sum_{u \in c-2} (l_x-1) = |c-2| * (l_x-1)

    For each u \in c-1, if l_x > 2, then \sum_{u \in c-1} (l_x-2) = |c-1| * (l_x-2)

    """
    # 1 <= level_id <= level_num - 1 , it makes nonsense to choose root.
    for level_id in range(level_num - 1, 0, -1):
        for u, child_set in lev_net[level_id].iteritems():
            subtree_size = 1  # |T_u|
            c_3_size = 0  # \sum_{v \in c-3} |T_v|
            c_2_size = 0  # |c-2|
            c_1_size = 0  # |c-1|

            for nbor in adj_table[u].iterkeys():
                if nbor in child_set:
                    subtree_size += node_subtree_size_map[nbor]
                elif nbor in lev_net[level_id + 1]:
                    c_3_size += node_subtree_size_map[nbor]
                elif nbor in lev_net[level_id]:
                    c_2_size += 1
                elif nbor in lev_net[level_id - 1]:
                    c_1_size += 1

            node_subtree_size_map[u] = subtree_size

            low_bound = 0  # lower bound of marginal reward
            c_3_size += subtree_size  # do not forget this
            low_bound += (c_3_size * level_id)
            if level_id > 2:
                low_bound += (c_1_size * (level_id - 2))
            if level_id > 1:
                low_bound += (c_2_size * (level_id - 1))

            heapq.heappush(h, (low_bound, u))

            # We only keep the k = candidate largest bonus nodes.
            if len(h) == (candidate_num + 1):
                heapq.heappop(h)

    # remember to pop the empty dictionary
    lev_net.pop()

    return [item[1] for item in h]


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
                               candidate_num,
                               idx):
    """
    :param adj_table: {node_id: {nbor_id: weight}, ...}

    :param monitors: [..., monitor_k, ...]

    :param ttl_dist: total distance of monitors

    :param candidate_num:

    :param idx:

    :return: new penalty(total distance).
    [monitor_1, ..., monitor_(idx-1), u, monitor_(idx+1), ...]
    We generate candidates_num candidates for u. And choose the best one.
    """
    # Generate candidates for u
    fixed_monitors = monitors[0:idx] + monitors[idx + 1:]

    level_net = get_random_lev_net(adj_table, fixed_monitors, seed=1)

    candidates = get_candidates(adj_table,
                                level_net,
                                candidate_num)

    node_root_dist_map = get_node_root_dist_map(level_net)
    fixed_monitors_ttl_dist = sum(node_root_dist_map.itervalues())

    # Find the best candidate
    for candidate in candidates:
        tmp_ttl_dist = fast_get_ttl_dist(adj_table,
                                         node_root_dist_map,
                                         fixed_monitors_ttl_dist,
                                         [candidate])
        if ttl_dist > tmp_ttl_dist:
            ttl_dist = tmp_ttl_dist
            monitors[idx] = candidate

    return ttl_dist


def improve_init_sol(adj_table,
                     init_sol,
                     maximal_iter_step,
                     candidate_num
                     ):
    """
    :param adj_table: {node_id: {nbor_id: weight}}

    :param init_sol:  [..., node_k, ...]

    :param maximal_iter_step:  For init_sol, we improve it at most iter_num steps.
    For each step, we improve along 0, 1, ..., len(init_sol)-1 index respectively.

    :param candidate_num:
    :return: Total dist of the improved solution. Note we will modify the init_sol in place.
    """

    """
    It is important to shallow copy the init_sol. 
    We can't modify the init_sol.
    """
    step = 0
    ttl_dist = get_ttl_dist(adj_table, init_sol)

    last_update_idx = None
    while True:
        variation = 0
        for idx in range(0, len(init_sol)):
            """
            In the get_coordinate_improvement, we find the best candidate.
            idx = last_update_idx means that no change will happen.  
            """
            if idx == last_update_idx:
                break

            new_ttl_dist = get_coordinate_improvement(adj_table,
                                                      init_sol,
                                                      ttl_dist,
                                                      candidate_num,
                                                      idx)
            if new_ttl_dist < ttl_dist:
                last_update_idx = idx

            variation += (ttl_dist - new_ttl_dist)
            ttl_dist = new_ttl_dist

        # print 'step: ' + str(step) + ' \t variation: ' + str(variation)
        step += 1
        if variation <= stop_criteria or step == maximal_iter_step:
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

    node_num = len(adj_table)

    """
    For each search, we generate candidate_num new
    candidates.
    """
    candidate_num = get_improvement_candidate_num(node_num)

    """
    For each initial solution, we improve it at most maximal_iter_step.
    For each step, we improve along each index respectively.
    """
    maximal_iter_step = get_improvement_maximal_iter_step(node_num)

    monitors = []
    ttl_dist = None

    trunc_idx = 1
    while trunc_idx <= trunc_num:
        """
        Note that in func improve_init_sol, we will modify sol
        in place. Thus the shallow copy is very important.
        """
        sol = init_sol[0:trunc_step * trunc_idx]
        ttl_dist = improve_init_sol(adj_table,
                                    sol,
                                    maximal_iter_step,
                                    candidate_num
                                    )

        monitors.append(sol)
        trunc_idx += 1

    return monitors, ttl_dist


def do_improve_init_sols_job(monitor_list, sub_pipe):
    """
    :param monitor_list: [..., monitor_k,...]
    :param sub_pipe: Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.
    :return:
    """
    """
    monitor_pattern(reference pattern):
    [graph_name_str, monitor_info_fmt, monitor_str] 
    """

    """
    Instantiate init_sol_pattern from instances of monitor_pattern.
    
    init_sol_pattern: 
                       ********************  *********************                                     
    [graph_name_str,   tree_method_info_str, init_sol_monitor_info, init_sol_str]
    
    """

    init_sol_list = get_instances(monitor_pattern,
                                  init_sol_pattern,
                                  monitor_list,
                                  sep)

    """
    Instantiate monitor_msg_pattern from instances of monitor_pattern.
    monitor_msg_pattern: 
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

    related_graph_id_list = get_graph_instances(graph_dir,
                                                graph_name_str,
                                                monitor_list,
                                                monitor_pattern,
                                                sep)

    for i in range(0, len(monitor_list)):

        """
        Load graph_title.
        """
        graph_path = os.path.join(graph_dir, related_graph_id_list[i])
        adj_table = get_adjtable(graph_path)

        """
        Instantiate tree_method_info_str, init_sol_monitor_info_str.
        """
        node_num = len(adj_table)
        tree_num = get_tree_num(node_num)
        init_sol_list[i] = init_sol_list[i].replace(tree_method_info_str,
                                                    tree_num_method.format(tree_num))
        max_monitor_num = get_max_monitor_num(node_num)
        init_sol_list[i] = init_sol_list[i].replace(init_sol_monitor_info_str,
                                                    max_monitor_num_method.format(max_monitor_num))

        """
        Load initial solution.
        """
        init_sol_path = os.path.join(init_sol_dir, init_sol_list[i])
        init_sol = pickle_from_disk(init_sol_path)

        """
        Improve initial solution and write to disk.
        """
        start_time = clock()
        monitors, penalty = improve_init_sols(adj_table, init_sol, *trunc_num_step_list[i])
        end_time = clock()

        monitor_path = os.path.join(monitor_dir, monitor_list[i])
        pickle_to_disk(monitor_path, monitors)

        """
        Instantiate penalty_str and elapsed_time_str in monitor_msg_pattern.
        """
        msg_list[i] = msg_list[i].replace(penalty_str, str(penalty))
        msg_list[i] = msg_list[i].replace(elapsed_time_str,
                                          str(get_elapsed_minute(start_time, end_time)))

        msg_list[i] = format_message(msg_list[i], sep)
        print msg_list[i]

    if sub_pipe:
        sub_pipe.send(msg_list)

