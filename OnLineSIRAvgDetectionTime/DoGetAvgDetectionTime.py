import sys
sys.path.extend(['../../'])

from Code.Tools import get_job
from Code.Tools import get_name
from Code.Tools import update_graph_scale_log
from Code.Tools import assign_job
from Code.Tools import run_multi_process
from Code.Tools import write_log
from GetAvgDetectionTime import do_get_avg_detection_time_job
from Config import *
from PatternConfig import *


if __name__ == '__main__':

    graph_name_list = [get_name(graph_id) for graph_id in graph_id_list]

    """
    0. Update scale_list
    1. scale[0] = |V|, use this information to get max monitor number.
    2. Use max monitor number and trunc_point_num to get step.
    """
    scale_list = update_graph_scale_log(graph_dir, graph_id_list, graph_scale_log_path)
    max_monitor_num_list = [get_max_monitor_num(node_num)
                            for node_num, edge_num in scale_list]

    step_list = [get_step(max_monitor_num)
                 for max_monitor_num in max_monitor_num_list]

    trunc_num_step_list = [trunc_num_step_fmt.format(trunc_point_num, step)
                           for step in step_list]

    job_list = []
    job_info_list = [graph_name_list,
                     trunc_num_step_list,
                     [infection_info_instant] * len(graph_name_list),
                     [str(snapshot_num)] * len(graph_name_list),
                     [avg_detection_time_str] * len(graph_name_list)]

    job_list = get_job(job_info_list, sep, avg_detection_time_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_get_avg_detection_time_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)

    if messages:
        write_log(avg_detection_time_log_path, messages)












































