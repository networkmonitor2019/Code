from Code.GeneralConfig.PatternConfig import *

"""
tree_method_info_str will be instantiated as tree-num_method-name which means that we 
use tree-num trees and method-name to estimate total distance.
"""
tree_method_info_str = 'tree_method_info'
node_ttl_dist_map_str = 'ttl_dist_map'

node_ttl_dist_map_pattern = sep.join([graph_name_str,
                                      tree_method_info_str,
                                      node_ttl_dist_map_str])


node_ttl_dist_map_msg_pattern = sep.join([graph_name_str,
                                          tree_method_info_str,
                                          elapsed_time_str])


init_sol_pattern = sep.join([graph_name_str,
                             tree_method_info_str,
                             init_sol_monitor_info_str,
                             init_sol_str])

init_sol_msg_pattern = sep.join([graph_name_str,
                                 tree_method_info_str,
                                 init_sol_monitor_info_str,
                                 penalty_str,
                                 elapsed_time_str])
