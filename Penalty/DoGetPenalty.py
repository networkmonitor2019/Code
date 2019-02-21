import sys
sys.path.extend(['../../'])

from Code.Tools import get_name
from Code.Tools import assign_job
from Code.Tools import run_multi_process
from Code.Tools import write_log
from Code.Tools import update_graph_scale_log
from GetPenalty import do_get_penalty_job
from Code.Tools import get_job


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
    step_list = [get_step(item) for item in max_monitor_num_list]

    trunc_num_step_list = [trunc_num_step_fmt.format(trunc_point_num, step) for step in step_list]

    job_info_list = [graph_name_list,
                     trunc_num_step_list,
                     [penalty_str] * len(graph_name_list)
                     ]

    job_list = get_job(job_info_list, sep, penalty_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_get_penalty_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)

    if messages:
        write_log(penalty_log_path, messages)




















