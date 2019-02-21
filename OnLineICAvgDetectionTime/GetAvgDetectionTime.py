from random import random
from random import sample
from Config import *
from PatternConfig import *
from operator import add

from Code.Tools import get_graph_instances
from Code.Tools import get_instances
from Code.Tools import write_to_disk
from Code.Tools import pickle_from_disk
from Code.Tools import get_adjtable
from Code.Tools import pickle_to_disk


def record_detection_time(new_infected_nodes, step, monitors, detec_time):
    """
    :param new_infected_nodes: list
    :param step:
    :param monitors: [... monitor_j ...]
    :param detec_time: [... detec_time_j ...]
    :return:
    """
    for u in new_infected_nodes:
        for j in range(0, len(monitors)):
            if detec_time[j] is None and u in monitors[j]:
                detec_time[j] = step


def simulate_ic(adj_table, monitors):
    """
    We simulate IC process on the graph_title (We do not consider multiple edges !!!!).
    And record the detection time for each monitor of monitors simultaneously.
    :param adj_table: {node:{nbor: weight}}
    :param monitors: [... monitor_j ...]
    :return:
    """

    """
    Initialize detec_time
    """
    detec_time = [None] * len(monitors)

    sources = sample(adj_table, 1)

    record_detection_time(sources, 0, monitors, detec_time)

    infected_nodes = {sources[0]}

    step = 1
    while sources:
        node_inf_nbor_num_map = {}
        """
        If u is infected, check each edge (u, v) incident to u.
        For each node u, u will only appear in sources at most once.
        """
        for u in sources:
            for v in adj_table[u]:
                if v not in infected_nodes:
                    node_inf_nbor_num_map[v] = node_inf_nbor_num_map.setdefault(v, 0) + 1

        sources = []
        for v in node_inf_nbor_num_map:
            inf_prob = 1 - (1 - activation_prob) ** node_inf_nbor_num_map[v]
            if random() < inf_prob:
                sources.append(v)
                infected_nodes.add(v)

        record_detection_time(sources, step, monitors, detec_time)

        if all(detec_time):
            return detec_time, len(infected_nodes)

        step += 1

    for i in range(0, len(detec_time)):
        if detec_time[i] is None:
            detec_time[i] = step + 1

    return detec_time, len(infected_nodes)


def get_avg_detection_time(adj_table, monitors, total_simu_round):
    """
    :param adj_table: {node:{nbor: weight}}
    :param monitors: [... monitor_j ...]
    :param total_simu_round: total simulation round
    :return:
    """

    """
    Change each monitor to set.
    """
    for i in range(0, len(monitors)):
        monitors[i] = set(monitors[i])

    """
    Average detection time
    """
    avg_detec_time = [0] * len(monitors)

    counter = 0
    trail_num = 0  # number of consecutive trails

    while counter < total_simu_round:

        while trail_num < alert_round:
            detec_time, infected_node_num = simulate_ic(adj_table, monitors)

            if infected_node_num > len(adj_table) * infection_ratio:
                trail_num = 0
                break
            else:
                trail_num += 1

        if trail_num == alert_round:
            avg_detec_time = None
            print 'Infection ratio cannot be reached within {0:d} rounds'.format(alert_round)
            break

        avg_detec_time = map(add, avg_detec_time, detec_time)
        counter += 1

    if avg_detec_time:
        avg_detec_time = [round(float(item) / total_simu_round, 2) for item in avg_detec_time]

    return avg_detec_time


def do_get_avg_detection_time_job(avg_detec_time_list, sub_pipe):
    """
    :param avg_detec_time_list: [... avg_detec_time_id ...],
    :param sub_pipe:
    :return:
    """

    """
    avg_detection_time_pattern:
    [graph_name_str, 
     trunc_num_step_str, 
     infection_info_str, 
     snapshot_num_str,
     avg_detection_time_str]

    monitor_pattern:
                     ****************
    [graph_name_str, monitor_info_str, monitor_str]
    """
    graph_id_list = get_graph_instances(graph_dir,
                                        graph_name_str,
                                        avg_detec_time_list,
                                        avg_detection_time_pattern,
                                        sep)

    trunc_num_step_list = get_instances(avg_detection_time_pattern,
                                        trunc_num_step_str,
                                        avg_detec_time_list,
                                        sep)

    monitor_list = get_instances(avg_detection_time_pattern,
                                 monitor_pattern,
                                 avg_detec_time_list,
                                 sep)

    msg_list = [None] * len(avg_detec_time_list)

    for graph_id_idx in range(0, len(graph_id_list)):
        graph_id = graph_id_list[graph_id_idx]
        trunc_num_step = trunc_num_step_list[graph_id_idx]
        monitor_id = monitor_list[graph_id_idx]
        avg_detec_time_id = avg_detec_time_list[graph_id_idx]

        """
        Make sure the existence of graph_title file.
        """
        graph_path = path.join(graph_dir, graph_id)

        if not path.exists(graph_path):
            msg_list[graph_id_idx] = 'Missing {0:s}. Cannot finish {1:s}'. \
                format(graph_path, avg_detec_time_id)

            print msg_list[graph_id_idx]
            continue

        """
        Make sure the existence of related monitor file.
        """
        monitor_info_list = [monitor_info_fmt.format(trunc_num_step, method)
                             for method in methods]

        monitor_id_list = [monitor_id.replace(monitor_info_str, monitor_info)
                           for monitor_info in monitor_info_list]

        monitor_paths = [path.join(monitor_dir, monitor_id) for monitor_id in monitor_id_list]

        chk_res = [path.exists(monitor_path) for monitor_path in monitor_paths]
        if not all(chk_res):
            msg_list[graph_id_idx] = 'Missing monitor. Cannot finish {0:s}'. \
                format(avg_detec_time_id)
            print msg_list[graph_id_idx]
            continue

        """
        Now, all related files exist.
        """
        avg_detec_time_path = path.join(avg_detection_time_dir, avg_detec_time_id)
        adj_table = get_adjtable(path.join(graph_dir, graph_id))

        """
        monitors = [
                    ...
                    ... 
                    [step * 1] ... [step * trunc_point_num] ---- method_k
                    ...
                    ... 
                   ]
        """
        monitors = []
        for monitor_path in monitor_paths:
            monitors.extend(pickle_from_disk(monitor_path))

        """
        res = [
                 ...
                 res_1, ..., res_(trunc point num) ---- method_k
                 ...
              ]
        """
        res = [round(float(item), 2) for item in get_avg_detection_time(adj_table, monitors, snapshot_num)]

        """
        Construct message.
        avg_detection_time_pattern:
        [graph_name_str, trunc_num_step_str, infection_info_str, snapshot_num_str, avg_detection_time_str]
        """
        msg_parts = avg_detec_time_id.split(sep)

        msg_content = '{0:s}:{1:s}:{2:s}:{3:s}\n'.format(msg_parts[0],
                                                         msg_parts[1],
                                                         msg_parts[2],
                                                         msg_parts[3]
                                                         )

        base_method = methods[0]
        base_line = res[trunc_point_num - 1]
        msg_content += '{0:s}:{1:.2f}\n'.format(base_method, base_line)

        for mtd_idx in range(1, len(methods)):
            tmp = (mtd_idx + 1) * trunc_point_num - 1
            msg_content += '{0:s}:{1:.2f} ({2:.2f}%)\n'.format(methods[mtd_idx],
                                                               res[tmp],
                                                               ((res[tmp] - base_line) * 100.0) / base_line)

        msg_list[graph_id_idx] = msg_content
        print msg_content

        if trunc_point_num > 1:
            """
            res = [
                        ...
                        res_1, ..., res_(trunc point num) ---- method_k
                        ...
                      ]
            """
            pickle_to_disk(avg_detec_time_path, res)
        elif trunc_point_num == 1:
            """
            Baseline and stretch ratio.
            """
            write_to_disk(avg_detec_time_path, msg_content)

    if sub_pipe:
        sub_pipe.send(msg_list)










