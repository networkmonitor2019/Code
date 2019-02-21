from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk
from Code.Tools import get_adjtable
from Code.Tools import get_ttl_dist
from Code.Tools import get_instances
from Code.Tools import get_graph_instances
from Code.Tools import write_to_disk

from Config import *
from PatternConfig import *

from os import path


def get_penalty(adj_table,
                monitors):
    """
    :param adj_table: {node_id: {nbor_id: weight}}
    :param monitors: [... monitor_j ...]
    :return:
    """
    return [get_ttl_dist(adj_table, monitor) for monitor in monitors]


def do_get_penalty_job(penalty_list, sub_pipe=None):
    """
    :param penalty_list: [... penalty_k ...],

    :param sub_pipe: Corresponding to a master pipe owned by the master process,
    if sub_pipe is not empty, we put some information into it and send to the master pipe.

    :return: write [..., penalty val_(i*scale) , ...] to penalty_path
    penalty val_(i*scale) : the penalty value of i*scale monitor
    """

    """
    penalty pattern: 
    [graph_name_str, trunc_num_step_str, penalty_str]
    
    monitor pattern:
                     ****************
    [graph_name_str, monitor_info_str, monitor_str]
        
    """
    trunc_num_step_list = get_instances(penalty_pattern,
                                        trunc_num_step_str,
                                        penalty_list,
                                        sep)

    monitor_list = get_instances(penalty_pattern,
                                 monitor_pattern,
                                 penalty_list,
                                 sep)

    graph_id_list = get_graph_instances(graph_dir,
                                        graph_name_str,
                                        penalty_list,
                                        penalty_pattern,
                                        sep)

    msg_list = [None] * len(penalty_list)

    for graph_id_idx in range(0, len(graph_id_list)):
        graph_id = graph_id_list[graph_id_idx]
        trunc_num_step = trunc_num_step_list[graph_id_idx]
        monitor_id = monitor_list[graph_id_idx]
        penalty_id = penalty_list[graph_id_idx]

        """
        Make sure the existence of graph_title file.
        """
        graph_path = path.join(graph_dir, graph_id)

        if not path.exists(graph_path):
            msg_list[graph_id_idx] = 'Missing {0:s}. Cannot finish {1:s}'.\
                format(graph_path, penalty_id)

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
                format(penalty_id)
            print msg_list[graph_id_idx]
            continue

        """
        Now, all related files exist.
        """
        penalty_path = path.join(penalty_dir, penalty_id)
        adj_table = get_adjtable(graph_path)

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
        res = [round(float(item), 2) for item in get_penalty(adj_table, monitors)]

        """
        Construct message.
        penalty pattern: 
        [graph_name_str, trunc_num_step_str, penalty_str]
        """

        msg_parts = penalty_id.split(sep)

        msg_content = '{0:s}:{1:s}:{2:s}\n'.format(msg_parts[0],
                                                   msg_parts[1],
                                                   msg_parts[2],
                                                   )

        base_method = methods[0]
        base_line = res[trunc_point_num-1]
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
            pickle_to_disk(penalty_path, res)
        elif trunc_point_num == 1:
            """
            Baseline and stretch ratio.
            """
            write_to_disk(penalty_path, msg_content)

    if sub_pipe:
        sub_pipe.send(msg_list)










































































































