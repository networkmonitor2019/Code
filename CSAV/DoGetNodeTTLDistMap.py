import sys
sys.path.extend(['../../'])

from Code.Tools import get_job
from Code.Tools import assign_job
from Code.Tools import run_multi_process
from Code.Tools import get_name
from Code.Tools import write_log
from Code.Tools import update_graph_scale_log

from Config import *
from PatternConfig import *
from GetNodeTTLDistMap import do_get_node_ttl_dist_map_job


if __name__ == '__main__':

    graph_name_list = [get_name(graph_id) for graph_id in graph_id_list]
    scale_list = update_graph_scale_log(graph_dir, graph_id_list, graph_scale_log_path)
    node_num_list = [scale[0] for scale in scale_list]
    tree_num_method_list = [tree_num_method.format(get_tree_num(node_num))
                            for node_num in node_num_list]

    """
    Instantiate node total distance map pattern:
    [graph_name_str, tree_method_info_str, node_ttl_dist_map_str]
    
    """
    node_ttl_dist_map_info_list = [graph_name_list,
                                   tree_num_method_list,
                                   [node_ttl_dist_map_str]*len(graph_name_list)]

    job_list = get_job(node_ttl_dist_map_info_list, sep, node_ttl_dist_map_dir)

    job_assign_res, needed_cpu_num = assign_job(job_list, accessible_cpu_num)

    messages = run_multi_process(do_get_node_ttl_dist_map_job,
                                 needed_cpu_num,
                                 job_assign_res,
                                 is_communication=True)

    if messages:
        write_log(node_ttl_dist_map_log_path, messages)

    #  do_get_node_root_dist_maps_job(job_list)





































