import os
from Code.Tools import get_job
from Code.Tools import assign_job
from Code.Tools import get_name
from Code.Tools import run_multi_process
from Code.Tools import write_log
from Code.Tools import update_graph_scale_log

from Config import *
from PatternConfig import *
from GetInitSol import do_maximize_reward_job

if __name__ == '__main__':

    graph_name_list = [get_name(graph_id) for graph_id in graph_id_list]

    """
    scale_list  = [ ... (|V|, |E|) ...] corresponding to graph_id_list
    """
    scale_list = update_graph_scale_log(graph_dir, graph_id_list, graph_scale_log_path)
    node_num_list = [scale[0] for scale in scale_list]
    max_monitor_num_method_list = [max_monitor_num_method.format(get_max_monitor_num(node_num))
                                   for node_num in node_num_list]

    """
    The instantiation of initial solution pattern:
    [graph_name_str, init_sol_monitor_info_str, init_sol_str]
    """
    monitor_info_list = [graph_name_list,
                         max_monitor_num_method_list,
                         [init_sol_str] * len(graph_name_list)]

    job_list = get_job(monitor_info_list, sep, monitor_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_maximize_reward_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)
    if messages:
        write_log(monitor_log_path, messages)

    # do_maximize_reward_job(job_list)

