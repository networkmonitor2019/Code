import sys
sys.path.extend(['../../'])

from Code.Tools import get_job
from Code.Tools import assign_job
from Code.Tools import get_name
from Code.Tools import run_multi_process
from Code.Tools import write_log
from Code.Tools import update_graph_scale_log
from ImproveInitSol import do_improve_init_sols_job

from Config import *
from PatternConfig import *


if __name__ == '__main__':

    graph_name_list = [get_name(graph_id) for graph_id in graph_id_list]

    """
    0. Get the scale of network.
    1. scale[0] = |V|, use this information to get max monitor number.
    2. Use max monitor number and trunc_point_num to get trunc_step.
    3. Instantiate monitor_info_fmt.
    """
    scale_list = update_graph_scale_log(graph_dir, graph_id_list, graph_scale_log_path)
    max_monitor_num_list = [get_max_monitor_num(scale[0]) for scale in scale_list]
    trunc_step_list = [get_step(item) for item in max_monitor_num_list]
    trunc_num_step_method_list = [trunc_num_step_method.format(trunc_point_num, item)
                                  for item in trunc_step_list]

    """
    Instantiate monitor pattern:
    [graph_name_str, monitor_info_fmt, monitor_str]
    
    """
    monitor_list = [graph_name_list,
                    trunc_num_step_method_list,
                    [monitor_str] * len(graph_name_list)
                    ]

    job_list = get_job(monitor_list, sep, monitor_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_improve_init_sols_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)

    if messages:
        write_log(monitor_log_path, messages)

    # do_improve_random_init_sols_job(job_list)

