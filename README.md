We create an automated manner to run the code.

The first step is to config the GeneralConfig/config.py. The most important items are:
(1) general_dir: we suppose anything of the data would under this directoty.
(2) graph_dir: the directory of networks. We suppose network is formatted as pure txt file, in which each line represents an edge.
(3) monitor_dir: the directory of monitors. Monitors generated by different methods will be stored under this directory.
Each monitor is pickled by python2 to be a list of list. Each inner list contains nodes, representing the nodes to monitor. The length of outer list is determined by trunc_point_num. step = max_minitor_num/trunc_point_num. Therefore, you will get the monitor in form: [ [ step * 1 nodes ], .. [step * trunc_point_num nodes]].
(4) accessible_cpu_num: the number of cpu avaiable in your computer. We use multi-process in the program.

The second step is to config the config.py in different modules. For example, if we want to run csav, we only need to config the CSAV/Config.py. An important parameter is graph_id_list meaning the network list we want to monitor. By default, they are all networks in graph_dir.

The third step is to tell the machine to do some job and we do not to modify anything. For example, if we want to run csav. Then we need to run DoGetNodeTTLDistMap.py to approximate total distance by rand. And then we need to run DoGetInitSol.py to get initial solutions for networks. Finally, we need to run DoImproveInitSol.py to improve our initial solutions. We can write a shell script to invoke them by sequence. Anyway, after we config properly in the first two steps, in this step we only need to invoke python script. 
