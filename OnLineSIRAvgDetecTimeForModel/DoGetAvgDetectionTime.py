import sys
sys.path.extend(['../../'])

from Code.Tools import get_job
from Code.Tools import assign_job
from Code.Tools import run_multi_process
from Code.Tools import write_log
from GetAvgDetectionTime import do_get_avg_detection_time_job
from Config import *
from PatternConfig import *


if __name__ == '__main__':

    scale_list = [get_scale_from_model_type(model) for model in model_list]
    max_monitor_num_list = [get_max_monitor_num(scale) for scale in scale_list]
    step_list = [get_step(item) for item in max_monitor_num_list]
    trunc_num_step_list = [trunc_num_step_fmt.format(trunc_point_num, step)
                           for step in step_list]

    job_info_list = [model_list,
                     trunc_num_step_list,
                     [infection_info_instant] * len(model_list),
                     [str(snapshot_num)] * len(model_list),
                     [avg_detection_time_str] * len(model_list)]

    job_list = get_job(job_info_list, sep, avg_detection_time_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_get_avg_detection_time_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)

    if messages:
        write_log(avg_detection_time_log_path, messages)












































