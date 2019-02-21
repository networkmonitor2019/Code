from random import random
from random import sample
from Config import *
from PatternConfig import *
from operator import add

from Code.Tools import get_instances
from Code.Tools import write_to_disk
from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk
from Code.Tools import get_adjtable
from Code.Tools import get_graph_instances

from itertools import product


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
    [model_type_str, trunc_num_step_str,
    infection_info_str, 
    snapshot_num_str, avg_detection_time_str]
    """

    models = get_instances(avg_detection_time_pattern,
                           model_type_str,
                           avg_detec_time_list,
                           sep)

    trunc_num_step_list = get_instances(avg_detection_time_pattern,
                                        trunc_num_step_str,
                                        avg_detec_time_list,
                                        sep)

    msg_list = [None] * len(avg_detec_time_list)

    for mdl_idx in range(0, len(models)):
        model = models[mdl_idx]
        avg_detec_time_id = avg_detec_time_list[mdl_idx]

        """
        Make sure the existence of related graph_title files.
        """
        graph_names = [unit_sep.join([model, str(iid)]) for iid in instance_num_range]

        graph_ids = get_graph_instances(graph_dir,
                                        graph_name_str,
                                        graph_names,
                                        graph_name_str,
                                        sep)

        graph_paths = [path.join(graph_dir, graph_id) for graph_id in graph_ids]

        chk_res = [path.exists(graph_path) for graph_path in graph_paths]
        if not all(chk_res):
            msg_list[mdl_idx] = 'Missing required graph_title files.' \
                          'Cannot finish {0:s}'.format(avg_detec_time_id)
            print msg_list[mdl_idx]

            continue

        """
        Make sure the existence of monitor files.
        """
        monitor_info_list = [monitor_info_fmt.format(trunc_num_step_list[mdl_idx],
                                                     method)
                             for method in methods]

        monitor_ids = [sep.join(item) for item in product(graph_names,
                                                          monitor_info_list,
                                                          [monitor_str])]

        monitor_paths = [path.join(monitor_dir, monitor_id) for monitor_id in monitor_ids]
        chk_res = [path.exists(monitor_path) for monitor_path in monitor_paths]
        if not all(chk_res):
            msg_list[mdl_idx] = 'Missing required monitor files.' \
                          'Cannot finish {0:s}'.format(avg_detec_time_id)
            print msg_list[mdl_idx]

            continue

        """
        Now, all related files exist.
        """
        avg_detec_time_path = path.join(avg_detection_time_dir, avg_detec_time_id)
        avg_res = [0] * (len(methods) * trunc_point_num)
        for j in range(0, len(graph_paths)):
            adj_table = get_adjtable(graph_paths[j])

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
            for monitor_path in monitor_paths[j*len(methods):(j+1)*len(methods)]:
                monitors.extend(pickle_from_disk(monitor_path))

            """
            avg_res = [
                    ...
                    res_1, ..., res_(trunc point num) ---- method_k
                    ...
                   ]
            """
            res = get_avg_detection_time(adj_table,
                                         monitors,
                                         snapshot_num
                                         )

            avg_res = map(add, avg_res, res)

        avg_res = [round(float(item) / len(graph_paths), 2) for item in avg_res]

        """
        Construct message.
        avg_detection_time_pattern:
        [model_type_str, trunc_num_step_str, infection_info_str, 
        snapshot_num_str, avg_detection_time_str]
        """

        msg_parts = avg_detec_time_id.split(sep)

        msg_content = '{0:s}:{1:s}:{2:s}-{3:s}:{4:s}\n'.format(msg_parts[0],
                                                               msg_parts[1],
                                                               msg_parts[2],
                                                               msg_parts[3],
                                                               msg_parts[4])

        base_method = methods[0]
        base_line = avg_res[trunc_point_num-1]
        msg_content += '{0:s}:{1:.2f}\n'.format(base_method, base_line)

        for mtd_idx in range(1, len(methods)):
            tmp = (mtd_idx + 1) * trunc_point_num - 1
            msg_content += '{0:s}:{1:.2f} ({2:.2f}%)\n'.format(methods[mtd_idx],
                                                               avg_res[tmp],
                                                               ((avg_res[tmp] - base_line) * 100.0) / base_line)

        msg_list[mdl_idx] = msg_content
        print msg_content

        if trunc_point_num > 1:
            """
            avg_res = [
                        ...
                        avg_res_1, ..., avg_res_(trunc point num) ---- method_k
                        ...
                      ]
            """
            pickle_to_disk(avg_detec_time_path, avg_res)
        elif trunc_point_num == 1:
            """
            Baseline and stretch ratio.
            """
            write_to_disk(avg_detec_time_path, msg_content)

    if sub_pipe:
        sub_pipe.send(msg_list)








