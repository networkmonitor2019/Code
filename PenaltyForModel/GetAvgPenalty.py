from Config import *
from PatternConfig import *
from operator import add

from Code.Tools import get_instances
from Code.Tools import write_to_disk
from Code.Tools import pickle_from_disk
from Code.Tools import pickle_to_disk
from Code.Tools import get_adjtable
from Code.Tools import get_ttl_dist
from Code.Tools import get_graph_instances
from itertools import product


def get_penalty(adj_table, monitors):
    """
    :param adj_table: {node:{nbor: weight}}
    :param monitors: [... monitor_j ...]
    :return:
    """
    return [get_ttl_dist(adj_table, monitor) for monitor in monitors]


def do_get_avg_detection_time_job(avg_penalty_list, sub_pipe):
    """
    :param avg_penalty_list: [... avg_penalty_id ...],
    :param sub_pipe:
    :return:
    """

    """
    avg_penalty_pattern:
    [model_type_str, trunc_num_step_str, penalty_str]
    
    monitor pattern:
     **************  ****************
    [graph_name_str, monitor_info_str, monitor_str]
    """

    models = get_instances(avg_penalty_pattern,
                           model_type_str,
                           avg_penalty_list,
                           sep)

    trunc_num_step_list = get_instances(avg_penalty_pattern,
                                        trunc_num_step_str,
                                        avg_penalty_list,
                                        sep)

    msg_list = [None] * len(avg_penalty_list)

    for mdl_idx in range(0, len(models)):
        model = models[mdl_idx]
        avg_penalty_id = avg_penalty_list[mdl_idx]

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
                          'Cannot finish {0:s}'.format(avg_penalty_id)
            print msg_list[mdl_idx]

            continue

        """
        Make sure the existence of related monitor files.
        """
        monitor_info_list = [monitor_info_fmt.format(trunc_num_step_list[mdl_idx], method)
                             for method in methods]

        monitor_ids = [sep.join(item) for item in product(graph_names,
                                                          monitor_info_list,
                                                          [monitor_str])]

        monitor_paths = [path.join(monitor_dir, monitor_id) for monitor_id in monitor_ids]
        chk_res = [path.exists(monitor_path) for monitor_path in monitor_paths]

        if not all(chk_res):
            msg_list[mdl_idx] = 'Missing required monitor files.' \
                          'Cannot finish {0:s}'.format(avg_penalty_id)
            print msg_list[mdl_idx]

            continue

        """
        Now, all related files exist.
        """
        avg_penalty_path = path.join(penalty_dir, avg_penalty_id)
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
            avg_res = map(add, avg_res, get_penalty(adj_table, monitors))

        avg_res = [round(float(item) / len(graph_paths), 2) for item in avg_res]

        """
        Construct message.
        avg_penalty_pattern:  [model_type_str, trunc_num_step_str, penalty_str]
        """
        msg_parts = avg_penalty_id.split(sep)

        msg_content = '{0:s}:{1:s}:{2:s}\n'.format(msg_parts[0],
                                                   msg_parts[1],
                                                   msg_parts[2],
                                                   )

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
            pickle_to_disk(avg_penalty_path, avg_res)
        elif trunc_point_num == 1:
            """
            Baseline and stretch ratio.
            """
            write_to_disk(avg_penalty_path, msg_content)

    if sub_pipe:
        sub_pipe.send(msg_list)








