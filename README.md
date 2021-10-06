# No-hop
No-hop DHT utilizes the programable data plane to speed up the key value look up proccess for distributed hash tables.

## Initialize Network

No-hop has two versions, Forward, and Rewrite. Forward needs all switches to be programable while Rewrite only one. 

### Generate Initial Build Files

To generate a new rewrite experiment run:

```bash
$ cd initialize_system/
$ python No_hop_Network.py rewrite
```

To generate a new forward experiment run:

```bash
$ cd initialize_system/
$ python No_hop_Network.py rewrite
```

If ```rewrite_build_folders=1```in ```No_hop_Network.py``` The experiment folder will be in ````No_hop_<forward, rewrite>_0````, else if ```rewrite_build_folders=0``` a new folder will be created with the next free index so, ````No_hop_<forward, rewrite>_<free_index>````

For more on generating build files please refer to ```initialize_system/No_hop_Init_system.pdf```.

### Running Experiment

To run an experiment: 

```bash
$ cd initialize_system/<Build folder name>
$ make
```
This will start the network and mininet cli. 

In the mininet CLI to open a terminal for a host:


```bash
mininet> xterm host_name
```
![](figs/xterm.gif)
To see network:

```bash
mininet> net
```
![](figs/mininet_net.gif)

In a host xterm to run the No-hop_host program.

To run a client:

```bash
# python ../../No-hop_host.py c
```

To run a server without an ID (Will not run stabilize proccess until ID is assigned):

```bash
# python ../../No-hop_host.py
```

To assign an ID to a host, send with the client a message of type=1, ID=some id that sends to that host, message= join:ID that you want to assign.

![](figs/joinID.gif)

To run a test:

```bash
# python ../../No-hop_host.py t:<Number of times each ID should be sent>
```

![](figs/test.gif)

To run hosts that immediatly start to stabilize pass them their ID at start:

```bash
# python ../../No-hop_host.py ID
```

![](figs/stabilize.gif)

To leave mininet:

```bash
mininet> exit
```
then:

```bash
$ sudo mn -c
```
