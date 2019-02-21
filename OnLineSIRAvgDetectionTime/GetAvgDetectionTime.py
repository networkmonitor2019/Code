import random as rd
from math import pow
from operator import add

from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import get_graph_name_scale_map
from Code.Tools import get_adjtable
from Code.Tools import get_name
from Code.Tools import write_to_disk
from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk

from Config import *
from PatternConfig import *


def get_infected_nbor_num(adj_table, infected, node):
    """
    :param adj_table: {node:{nbor: weight}}
    :param infected:  set([..., node_k, ...])
    :param node:
    :return: number of infected neighbor of node
    """
    infected_nbor_num = 0
    for nbor in adj_table[node]:
        if nbor in infected:
            infected_nbor_num += adj_table[node][nbor]

    return infected_nbor_num


def is_get_infected(infected_nbor_num):
    """
    :param infected_nbor_num:
    :return: the probability of node to be infected is 1 - (1-infection_prob)**infected_nbor_num.
    We get a random number \in [0,1), if this number is less than the probability,
    then return True, else return False.
    """

    if rd.random() < 1 - pow(1-infection_prob, infected_nbor_num):
        return True

    return False


def simulate_infection_process(adj_table,
                               new_infected_nodes,
                               risk_nodes,
                               suspected,
                               infected,
                               ):
    """
    :param adj_table: {node:{nbor: weight}}
    :param new_infected_nodes: [..., node_k,...]. Nodes that infected in latest round.
    :param risk_nodes: set([..., node_k,...]). Nodes that has infected neighbor.
    :param suspected:
    :param infected:
    :return:
    """
    """
    For new infected node u, if it is neighbor v is suspected, then v is a high risk node.
    """
    for node in new_infected_nodes:
        for nbor in adj_table[node]:
            if nbor in suspected:
                risk_nodes.add(nbor)

    """
    For each high risk node u, we check the number of infected neighbor of u. 
    If the number is 0, which means the infected neighbors of u are recovered, then u will not be a high risk
    node any longer.
    If the number > 0, we further decide u will be infected or not. If u is infected, then it is no longer a 
    high risk node and regarded as the newly infected node.
    """
    new_infected_nodes = set()

    # node that has no risk or is infected.
    no_risk_or_new_infected_nodes = set()

    for node in risk_nodes:

        infected_nbor_num = get_infected_nbor_num(adj_table, infected, node)

        # the node has no risk any more.
        if infected_nbor_num == 0:
            no_risk_or_new_infected_nodes.add(node)
            continue

        if is_get_infected(infected_nbor_num):
            new_infected_nodes.add(node)

    no_risk_or_new_infected_nodes.update(new_infected_nodes)
    risk_nodes.difference_update(no_risk_or_new_infected_nodes)

    return new_infected_nodes, risk_nodes


def simulate_recover_process(infected, recovered):
    """
    :param infected: set([... node_k ...]). Infected nodes.
    :param recovered: set([... node_k ...]). Recovered nodes.
    :return:
    """
    for node in infected.copy():
        if rd.random() < recovery_prob:
            infected.remove(node)
            recovered.add(node)


def record_detection_time(new_infected_nodes, step, monitors, detec_time):
    """
    :param new_infected_nodes: set
    :param step:
    :param monitors: [... monitor_j ...]
    :param detec_time: [... detec_time_j ...]
    :return:
    """
    for u in new_infected_nodes:
        for j in range(0, len(monitors)):
            if detec_time[j] is None and u in monitors[j]:
                detec_time[j] = step


def simulate_sir(adj_table, monitors):
    """
    We simulate SIR process on the graph_title.
    And record the detection time for each monitor of monitors simultaneously.
    :param adj_table: {node:{nbor: weight}}
    :param monitors: [... monitor_j ...]
    :return:
    """

    # recovered nodes
    recovered = set()

    # choose the source for SIR
    nodes = adj_table.keys()
    source = rd.choice(nodes)
    # infected nodes
    infected = {source}
    # suspected nodes
    suspected = set(nodes)
    suspected.remove(source)

    new_infected_nodes = {source}
    # {u : u has infected nodes surrounding it.}
    risk_nodes = set()

    infected_node_num = 1


    """
    Initialize detec_time
    """
    detec_time = [None] * len(monitors)

    record_detection_time(new_infected_nodes, 0, monitors, detec_time)

    if all(detec_time):
        return detec_time, infected_node_num

    step = 1
    while infected:
        new_infected_nodes, risk_nodes = simulate_infection_process(adj_table,
                                                                    new_infected_nodes,
                                                                    risk_nodes,
                                                                    suspected,
                                                                    infected,
                                                                    )
        simulate_recover_process(infected, recovered)

        infected.update(new_infected_nodes)
        suspected.difference_update(new_infected_nodes)

        record_detection_time(new_infected_nodes, step, monitors, detec_time)
        infected_node_num += len(new_infected_nodes)

        if all(detec_time):
            return detec_time, infected_node_num

        step += 1

    for i in range(0, len(detec_time)):
        if detec_time[i] is None:
           detec_time[i] = step

    return detec_time, infected_node_num


def get_avg_detection_time(adj_table,
                           monitors,
                           total_simu_round):

    """
    :param adj_table:  {u:{v: weight}}
    :param monitors: [... monitor_j ...]
    monitor_j is a list of nodes.
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
            detec_time, infected_node_num = simulate_sir(adj_table, monitors)

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
        avg_detec_time = [round(float(item)/total_simu_round, 2) for item in avg_detec_time]

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





















