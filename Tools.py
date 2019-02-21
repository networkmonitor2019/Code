import sys
import os
import errno
import pickle as pkl
from multiprocessing import Process
from multiprocessing import Pipe
from math import log
from itertools import product
from time import strftime
from random import sample


def get_type(path):
    """
    :param path:
    eg. a/b/123.txt
    eg. a/b/10000_4_0
    :return:
    type of the file in path.
    eg. txt
    eg. pickle
    We consider only TXT
    """
    obj_id = path.split(os.sep)[-1]  # obj_id = obj_name.obj_type
    if obj_id[-4:] == '.txt':
        return 'txt'
    else:
        return 'pickle'


def get_name(path):
    """
    :param path:
    eg. a/b/123.txt
    eg. a/b/10000_4_0
    :return:
    eg. 123
    eg. 10000_4_0
    """
    obj_id = path.split(os.sep)[-1]
    obj_type = get_type(path)
    if obj_type == 'txt':
        obj_name = obj_id[0: -4]
    else:
        obj_name = obj_id
    return obj_name


def get_adjtable(path):
    """
    :param path: path of the network.
    :return: adjacent table of the network.
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    """
    obj_type = get_type(path)
    if obj_type != 'txt':
        adj_table = pickle_from_disk(path)
    else:
        adj_table = {}
        input_file = open(path, 'r')
        for line in input_file:
            node_1, node_2 = line.strip().split()
            adj_table[node_1][node_2] = adj_table.setdefault(node_1, {}).setdefault(node_2, 0) + 1
            adj_table[node_2][node_1] = adj_table.setdefault(node_2, {}).setdefault(node_1, 0) + 1
        input_file.close()
    return adj_table


def write_adjtable_to_txt(path, adj_table):
    """
    :param path: output path of adj_table
    :param adj_table: {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :return: write adjtable into path.
    """
    output = ''
    for u in adj_table:
        for v in adj_table[u]:
            if u <= v:
                output += '{0:s}\t{1:s}\n'.format(u, v) * adj_table[u][v]

    output_file = open(path, 'w')
    output_file.write(output)
    output_file.close()


def get_graph_scale_from_file(file_path):
    """
    :param file_path: path of the network.
    :return: |V|,|E|
    """
    input_file = open(file_path, 'r')
    nodes = set([])
    edge_num = 0
    for line in input_file:
        u, v = line.strip().split()
        nodes.add(u)
        nodes.add(v)
        edge_num += 1
    input_file.close()
    return len(nodes), edge_num


def get_graph_name_scale_map(graph_scale_log_path):
    """
    :param graph_scale_log_path: Each line in graph scale log is formatted as
    "graph name \t node number \t edge number"
    :return: {graph_name: (node_number, edge_number)}
    """
    graph_scale_map = {}

    if not os.path.exists(graph_scale_log_path):
        return graph_scale_map

    input_file = open(graph_scale_log_path, 'r')
    for line in input_file:
        graph_name, node_num, edge_num = line.strip().split()
        graph_scale_map[graph_name] = (node_num, edge_num)

    input_file.close()
    return graph_scale_map


def update_graph_scale_log(graph_dir, graph_id_list, graph_scale_log_path):
    """
    :param graph_dir:
    :param graph_id_list:
    :param graph_scale_log_path:
    :return: scale list with each item corresponds to a graph_id in graph_id_list.
    """

    """
    Get graph_name_scale_map = {graph_name: (|V|, |E|)} from graph_scale_log_path.
    """
    graph_name_scale_map = get_graph_name_scale_map(graph_scale_log_path)

    scale_list = []
    name_scale_to_append = []
    for graph_id in graph_id_list:
        graph_name = get_name(graph_id)

        if graph_name not in graph_name_scale_map:
            node_num, edge_num = get_graph_scale_from_file(os.path.join(graph_dir, graph_id))
            name_scale_to_append.append((graph_name, node_num, edge_num))
        else:
            node_num = int(graph_name_scale_map[graph_name][0])
            edge_num = int(graph_name_scale_map[graph_name][1])
        scale_list.append((node_num, edge_num))

    """
    If there is anything to append, just append it.
    """
    if name_scale_to_append:
        output_content = ''
        for info in name_scale_to_append:
            graph_name, node_num, edge_num = info
            output_content += '{0:s}\t{1:d}\t{2:d}\n'.format(graph_name, node_num, edge_num)

        output_file = open(graph_scale_log_path, 'a+')
        output_file.write(output_content)
        output_file.close()

    return scale_list










def get_node_deg_map(adj_table, nodes):
    """
    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :param nodes: an iterable object.
    :return: a map from node in nodes to its degree.
    e.g. {u: w(u), ...} where w(u) = \sum_{v \in N(u)} w(u, v), N(u) is the neighbor set of u.
    """
    node_degree_map = {}
    for node in nodes:
        node_degree_map[node] = sum(adj_table[node].itervalues())
    return node_degree_map


def get_avg_deg(adj_table):
    """
    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :return: average degree of the network
    """
    ttl_deg = 0
    for node in adj_table:
        ttl_deg += sum(adj_table[node].itervalues())
    return float(ttl_deg)/len(adj_table)


def get_level_net(adj_table, roots):
    """
    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :param roots: an iterable object
    :return: a level network from roots by BFS
    # Example: [{a:set(b,c),.. }, {b:set(d),c:set()}, {d:set()}]
    # from left to right, it is level 0, 1, 2, .....
    """
    visited = set(roots)
    current_level = roots
    level_net = []
    while current_level:
        for u in current_level:
            visited.add(u)

        level = {}
        for u in current_level:
            level[u] = set()

        next_level = set()
        for u in current_level:
            for v in adj_table[u]:
                if v not in visited and v not in next_level:
                    next_level.add(v)
                    level[u].add(v)

        current_level = next_level
        level_net.append(level)

    return level_net


def get_ttl_dist(adj_table, nodes):
    """
    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :param nodes: an iterable object
    :return: total distance to other nodes from nodes
    """
    visited = set()
    current_level = nodes
    ttl_dist = 0
    level_dist = 0
    while current_level:
        for v in current_level:
            visited.add(v)
        ttl_dist += len(current_level) * level_dist
        next_level = set()
        for v in current_level:
            for w in adj_table[v].iterkeys():
                if w not in visited:
                    next_level.add(w)
        current_level = next_level
        level_dist += 1
    return ttl_dist


def pickle_to_disk(path, obj):
    """
    :param path: 
    eg. a/b/123.txt
    eg. a/b/10000_4_0
    :param obj: python object. dict or list and so on.
    :return: 
    """
    output_file = open(path, 'w')
    pkl.dump(obj, output_file)
    output_file.close()


def write_to_disk(path, content_str):
    """
    :param path:
    :param content_str: String.
    :return:
    """
    with open(path, 'w') as output_file:
        output_file.write(content_str)



def pickle_from_disk(path):
    """
    :param path:
    eg. a/b/123.txt
    eg. a/b/10000_4_0
    :return:
    """
    input_file = open(path, 'r')
    obj = pkl.load(input_file)
    input_file.close()
    return obj

def to_str(item):
    """
    :param item:
    :return: str(item)
    """
    if isinstance(item, str):
        return item
    if isinstance(item, float):
        return '{0:.2f}'.format(item)
    else:
        return str(item)

def get_str_list(ls):
    """
    :param ls: list of object
    :return: a list in which each term is a string and converted from ls
    """
    return [to_str(item) for item in ls]


def get_graph_instances(graph_dir, graph_name_str, instances, pattern, sep):
    """
    :param graph_dir: directory of graphs
    :param graph_name_str: the str to identify the position of graph name in pattern
    :param instances: [..., instance_i, ...]
    :param pattern: pattern of instance. Make sure the pattern contains graph_name_str
    e.g. "graph_name__q__p__t__simu_round__snapshot"
    :param sep: used to seperate instance and pattern
    :return: [..., graph_id_i, ...]
    graph_id_i is instance_i's graph id.
    """

    # put the graph name involved in instances together in a list
    graph_name_idx = pattern.split(sep).index(graph_name_str)
    graph_id_list = [None] * len(instances)
    for i in range(0, len(instances)):
        graph_id_list[i] = instances[i].split(sep)[graph_name_idx]

    # get the {graph name: type}
    graph_name_type_map = get_name_type_map(os.listdir(graph_dir))

    for i in range(0, len(instances)):
        if graph_name_type_map[graph_id_list[i]] == 'txt':
            graph_id_list[i] = graph_id_list[i] + '.txt'

    return graph_id_list






def get_edge_list(graph_path):
    """
    :param graph_path:
    :return: edge list of graph
    e.g. [..., (vi, vj), .... ]
    (vi, vj) represents an edge between vi and vj
    """
    input_file = open(graph_path, 'r')
    edge_list = []
    for line in input_file:
        edge_list.append(tuple(line.strip().split()))
    input_file.close()
    return edge_list


def get_struc_entropy_val(adj_table, comm_member_map):
    """

    :param adj_table: adjacent table
    e.g. {u:{v: w(u,v), ...}, v:{u:w(u,v), ...}, ...}
    :param comm_member_map: {comm: set([comm member])}
    :return: float value of two-dimension structure entropy
    """

    # {comm_id:vol}
    comm_vol_map = {}
    # {comm_id: cut edge num }
    comm_cut_edge_num_map = {}
    # {node_id: degree}
    degree = get_node_deg_map(adj_table, adj_table.iterkeys())
    # {node_id: comm_id}
    node_info = {}
    for comm_id in comm_member_map:
        for node_id in comm_member_map[comm_id]:
            node_info[node_id] = comm_id

    for comm_id in comm_member_map:
        vol = 0
        cut_edge_num = 0
        for node_id in comm_member_map[comm_id]:
            for nbor_id, weight in adj_table[node_id].iteritems():
                vol += weight
                if node_info[nbor_id] != comm_id:
                    cut_edge_num += weight
        comm_vol_map[comm_id] = vol
        comm_cut_edge_num_map[comm_id] = cut_edge_num

    ttl_vol = sum(degree.itervalues())

    struc_entropy_val = 0

    '''
    Two dimensional structure entropy
    part1: the average code length of node
    \sum_{j=1}^{L} \sum_{i \in P_j} d_i/2m * log (V_j/d_i)
    part2: the average code length of community 
    \sum_{j=1}^{L} g_j/2m * log(2m / V_j)
    Add these two parts together and by some simple calculation we get
    (1/2m) *  [ \sum_{j=1}^{L} (V_j - g_j) * log (V_j) + log (2m) * \sum_{j=1}^{L} g_j 
     - \sum_{i \in V} d_i * log (d_i) ] 
    '''

    # \sum_{j=1}^{L} (V_j - g_j) * log (V_j)
    for comm_id in comm_member_map:
        struc_entropy_val += (comm_vol_map[comm_id] - comm_cut_edge_num_map[comm_id]) * \
                              log(comm_vol_map[comm_id], 2)

    # \sum_{j=1}^{L} (V_j - g_j) * log (V_j) + log (2m) * \sum_{j=1}^{L} g_j
    struc_entropy_val += sum(comm_cut_edge_num_map.itervalues()) * log(ttl_vol, 2)

    # \sum_{j=1}^{L} (V_j - g_j) * log (V_j) + log (2m) * \sum_{j=1}^{L} g_j -\sum_{i \in V} d_i * log (d_i)
    for node_id in adj_table:
        struc_entropy_val -= degree[node_id] * log(degree[node_id], 2)

    struc_entropy_val /= ttl_vol
    return struc_entropy_val


def get_name_type_map(id_list):
    """
    :param id_list: [..., identity_k, ...]
    identity_K = name_k.type_k
    :return: {name_k: type_k ...}
    """
    name_type_map = {}
    for each_id in id_list:
        obj_name = get_name(each_id)
        obj_type = get_type(each_id)
        name_type_map[obj_name] = obj_type

    return name_type_map


def filter_job(job_list, res_dir):
    """
    :param job_list: [..., job_k, ...]
    :param res_dir:
    :return:
    """
    finished_job_set = set(os.listdir(res_dir))
    jobs = []
    for job in job_list:
        if job not in finished_job_set:
            jobs.append(job)

    return jobs


def get_job(job_info_list, joiner, res_dir):
    """
    :param job_info_list: [L_1, L_2, L_3, ..., L_K],
    where each L_i is a list. All lists in job_info_list should have
    same length.
    :param joiner: For each corresponding part of L_1, ..., L_K, join them by joiner.
    :param res_dir: used to remove the finished job.
    :return: Unfinished job list.
    """
    return filter_job([joiner.join(item) for item in zip(*job_info_list)], res_dir)


def assign_job(job_list, accessible_cpu_num):
    """

    :param job_list: [..., job_k, ....]
    :param accessible_cpu_num: Integer. Number of available CPU.
    :return: cpu_job_list_map = {cpu_id: [job_list] ...}, needed_cpu_num
    """

    ttl_job_num = len(job_list)
    cpu_job_list_map = {}
    if ttl_job_num > 0:
        if ttl_job_num < accessible_cpu_num:
            needed_cpu_num = ttl_job_num
        else:
            needed_cpu_num = accessible_cpu_num

        avg_job_num = ttl_job_num/needed_cpu_num
        for cpu_idx in range(0, needed_cpu_num, 1):
            cpu_job_list_map[cpu_idx] = job_list[cpu_idx * avg_job_num: (cpu_idx + 1) * avg_job_num]

        job_idx = needed_cpu_num * avg_job_num
        for idx in range(job_idx, ttl_job_num, 1):
            cpu_job_list_map[idx-job_idx].append(job_list[idx])
    else:
        needed_cpu_num = 0

    return cpu_job_list_map, needed_cpu_num


def run_multi_process(func, cpu_num, cpu_job_list_map, shared_para_tuple=(), is_communication=False):
    """
    :param func: func to run
    :param cpu_num: num of needed cpu
    :param cpu_job_list_map: {cpu_id: [job_list] ...}
    :param shared_para_tuple:(para1, para2, ...), paras used by all processes
    :param is_communication: If is_communication is True, then the main process
    should wait to receive some information from subprocess.
    :return:
    """

    if cpu_num > 0:
        process_list = []

        if not is_communication:
            for idx in range(0, cpu_num):
                p = Process(target=func, args=(cpu_job_list_map[idx],) + shared_para_tuple)
                p.start()
                process_list.append(p)

            for process in process_list:
                process.join()

            return None

        else:
            # master_pipe_list[i] and sub_pipe_list[i] are the two ends of pipe.
            # master_pipe_list[i] owned by master process and sub_pipe_list[i] owned by subprocess
            master_pipe_list = [None] * cpu_num
            sub_pipe_list = [None] * cpu_num

            content_list = []
            for idx in range(0, cpu_num):
                master_pipe_list[idx], sub_pipe_list[idx] = Pipe()
                p = Process(target=func, args=(cpu_job_list_map[idx],) + shared_para_tuple + (sub_pipe_list[idx],))
                p.start()

            for idx in range(0, cpu_num):
                # We assume that the type of received object is List.
                content_list += master_pipe_list[idx].recv()

            return content_list


def update_instance(pattern,
                    pattern_str,
                    instances,
                    replacer_list,
                    sep
                    ):
    """
    :param pattern:
    sep.join([... pattern_str_k ...])
    :param pattern_str:
    :param instances: [ ... instance_i ...]
    :param replacer_list:  [ ... replacer_i ...]
    :param sep:
    :return: For instance_i, replace value of pattern_str by replacer_i.
    """

    if pattern.find(pattern_str) == -1:
        return None

    pattern_list = pattern.split(sep)

    updated_instances = []
    loc = pattern_list.index(pattern_str)
    for i in range(0, len(instances)):
        instance_list = instances[i].split(sep)
        instance_list[loc] = replacer_list[i]
        updated_instances.append(sep.join(instance_list))

    return updated_instances


def get_instances(reference_pattern,
                  pattern,
                  reference_instances,
                  sep
                  ):
    """
    :param reference_pattern:
    sep.join([... pattern_str_k ...])

    :param pattern:
    sep.join([... pattern_str_i ...])

    :param reference_instances: a list of instance of reference pattern
    :param sep:

    :return: For each reference_instance, construct an instance as follows:
    If a field of pattern appears in reference pattern, we copy the corresponding value of
    reference instance into new instance.

    Otherwise, we just put the pattern str of pattern into new instance.
    """
    reference_pattern_list = reference_pattern.split(sep)
    pattern_list = pattern.split(sep)
    lenth = len(pattern_list)
    instances = []
    for reference_instance in reference_instances:
        reference_instance_list = reference_instance.split(sep)
        instance_list = [None] * lenth
        for i in range(0, lenth):
            if pattern_list[i] in reference_pattern_list:
                instance_list[i] = reference_instance_list[reference_pattern_list.index(pattern_list[i])]
            else:
                instance_list[i] = pattern_list[i]
        instances.append(sep.join(instance_list))

    return instances


def format_message(message, sep):
    """
    :param message: "... sep partL sep..."
    :return: take apart message and return a format string.
    """
    res = ""
    for part in message.split(sep):
        res += '{0:<16s}'.format(part)

    return res


def write_log(log_path, messages):
    """
    :param log_path:
    :param messages: [... message_k ...]
    :return:
    """
    output_file = open(log_path, 'a+')
    date = strftime('%Y-%m-%d-%H:%M:%S')
    content = date + '\n'
    for message in messages:
        content = content + message + '\n'

    output_file.write(content)
    output_file.close()


def get_elapsed_minute(start_time, end_time):
    """
    :param start_time: second
    :param end_time: second
    :return:
    """
    return round((end_time-start_time)/60, 2)


def get_largest_connected_comp_adjtable(adj_table):
    """
    :param adj_table: {u:{v: w(u,v)}, v:{u:w(u,v)}}
    :return: adj_table of largest connected component
    """
    """
    Initially, each node is not visited.
    """
    unvisited = set(adj_table.iterkeys())

    largest_connected_comp_size = 0
    largest_connected_comp = set()

    """
    If |largest_connected_comp| >= |unvisited|, then we already have found the 
    largest connected component. 
    """
    while largest_connected_comp_size < len(unvisited):

        current_level = set(sample(unvisited, 1))

        """
        The connected component from current level.
        """
        connected_comp = set()

        while current_level:
            next_level = set()
            for u in current_level:
                connected_comp.add(u)
                unvisited.remove(u)
                for v in adj_table[u]:
                    if v not in connected_comp and v not in current_level:
                        next_level.add(v)
            current_level = next_level

        if len(connected_comp) > largest_connected_comp_size:
            largest_connected_comp_size = len(connected_comp)
            largest_connected_comp = connected_comp

    """
    Construct the adjacent table from adj_table
    """
    largest_connected_comp_adj_table = {}
    for u in largest_connected_comp:
        largest_connected_comp_adj_table[u] = adj_table[u]

    return largest_connected_comp_adj_table


def create_dir(dir_path):
    """
    :param dir_path: the path of directory
    :return: create a directory at dir_path
    """
    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise









