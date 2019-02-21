We want to create an automated manner to run the code. The first step is to config the config.py in different directories.
(1) 



config scripts and drag the network files into correpsonding directory set in config, then run the script starting with "Do....". The name of output file is highly formatted and human readable.

We use multiprocess to deal with different network files, you can set the process number in GeneralConfig/Config.py.

Local Search, CSAV, CLC, DEG are methods to find monitors. AvgDetectionTime, AvgDetectionTimeForModel, Penalty are used to evaluate performance. SIRSimulation and ICSimulation are used to generate snapshots. Tools.py is very important, it includes many methods that are shared by other scripts.

After downloading, (1) please creat a new "Code" dir under "nmt", and move all files under nmt into "Code". (2) Set "nmt" to be the work dir for python.
