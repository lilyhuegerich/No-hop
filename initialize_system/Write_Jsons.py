import shutil
import json
import sys
import os
import networkx as nx


def make_no_hop_tables(network):
    """
    For all switches generate no_hop tables as dictionaries
    returns dict: {switch: switch_no_hop_table}
    """

    no_hop_tables={}
    for switch in network.switches:
        no_hop_tables[switch]=make_no_hop_table(network, switch)
    return no_hop_tables

def make_no_hop_table(network , switch):
    """
    For switch, generate no_hop table
    returns list of entries
    """

    connected=switch_connections(network, switch)
    no_hop_table={}
    up_tree=0
    for i in connected:
        if i in no_hop_table or i=="client":
            continue
        elif i in network.host_ids:
            no_hop_table[i]=(make_single_no_hop_table_entry(port=connected[i], range=network.host_range(i)))
            continue
        elif (range_size(network.reachable[switch])< range_size(network.reachable[i])):
            """
            The last range match for switches, sends the packet back up the tree
            """
            up_tree=(make_single_no_hop_table_entry(port=connected[i], range=(0, network.max_id+1)))
            continue
        else:
            for j in connected:
                if not (j==i or j=="client" or j in no_hop_table):
                    if network.reachable[i]==network.reachable[j]:
                        if (len(network.reachable[i])==2):
                            """
                            to minimize range fields, if range is already split just use the already given split point
                            """
                            no_hop_table[i]=make_single_no_hop_table_entry(port=connected[i], range=(network.reachable[i][0][0], network.reachable[i][0][1]))
                            no_hop_table[j]=make_single_no_hop_table_entry(port=connected[j], range=(network.reachable[i][1][0], network.reachable[i][1][1]))


                        elif (len(network.reachable[i])==1):
                            """
                            split range
                            """
                            split_point=0
                            total=0
                            for k in network.reachable[i]:
                                total+= k[1]-k[0]

                            split_point=total/2
                            no_hop_table[i]=make_single_no_hop_table_entry(port=connected[i], range=(network.reachable[i][0][0], network.reachable[i][0][0]+ split_point))
                            no_hop_table[j]=make_single_no_hop_table_entry(port=connected[j], range=(network.reachable[i][0][0] +split_point, network.reachable[i][0][1]))
                        else:
                            raise ValueError ("Either more than two ranges were found for reachable or there was a mistake while computing reachables")
                        break
            else:

                no_hop_table[i]=make_single_no_hop_table_entry(port=connected[i], range=(network.reachable[i]))

    no_hop_table=list(no_hop_table.values())
    if not up_tree==0:
        no_hop_table.append(up_tree)
    clean_no_hop_table=list()

    #if entries in sublists put them in list without sublist
    for i in no_hop_table:
        if type(i)==list:
            for j in i:
                clean_no_hop_table.append(j)
        else:
            clean_no_hop_table.append(i)

    #Check that all values are in the table
    for switch_range in network.reachable[switch]:
        for r in range(switch_range[0], switch_range[1]):
            if switch=="a":
                without_up_tree=clean_no_hop_table
            else:
                without_up_tree=clean_no_hop_table[:-1]
            for i in without_up_tree:
                if r in range(i["match"]["hdr.dht.id"][0], i["match"]["hdr.dht.id"][1]+1):
                    break
            else:
                print (without_up_tree)
                raise ValueError("value "+ str(r)+ " not in no-hop table for switch "+ str(switch)+ " with reachable range "+ str(network.reachable[switch]))
    return clean_no_hop_table

def range_size(range_list):
    """
    calculate total size of range_list
    """
    r_s=0
    for r in range_list:
        r_s+= r[1]- r[0]
    return r_s

def make_single_no_hop_table_entry ( port, range, group_id=1):
    """
    Make a single no hop table entry that sends range(tuple) out of port (int) and matches to group_id(int, default=1)
    returns entry as dict
    """
    if type(range)==tuple:
        table_entry = dict({"table":"ThisIngress.no_hop_lookup",
        "match":{
            "hdr.dht.group_id": group_id,
            "hdr.dht.id": (int(range[0]), int(range[1]))
            },
        "priority": 1,
        "action_name":"ThisIngress.no_hop_forward",
        "action_params":{"port": port}
        })
        return table_entry
    else:
        table_entry=[]
        for r in range:
            table_entry.append(make_single_no_hop_table_entry(port, r))
        return table_entry

def switch_connections(network, switch):
    """
    Return a dictionary {connection target: Outgoing port} for all connections that switch is in
    """
    connected={}
    for c_i, connection in enumerate(network.connections):
        if connection[0]==switch:
            connected[connection[1]]=network.connection_ports[c_i][0]
        elif connection[1]==switch:
            connected[connection[0]]=network.connection_ports[c_i][1]
    return connected

def formalize_switch(switch, s):
    """
    Create single entry for a switch in topology.json
    """
    entry= {
        "mac": "08:00:00:00:01:"+str(s),
        "runtime_json": "./build/"+switch+"P4runtime.json"
    }
    return entry

def formalize_switches(switches):
    """
    Create all entries for the switches in the topology.json
    """

    switches_formal=dict()
    for s, switch in enumerate(switches):
        switches_formal["s_"+switch]=formalize_switch(switch, s)
    return switches_formal

def formalize_connection_names(network):
    """
    Bring connections into a printable/ readable form for mininet
    """
    new_connections=[[0,0] for _ in range(len(network.connections))]
    for c, connection in enumerate(network.connections):
        if connection[0] in network.switches:
            new_connections[c][0]="s_"+str(connection[0])
        elif connection[0] in network.host_ids:
            new_connections[c][0]="h_"+str(connection[0])
        else:
            new_connections[c][0]="h_client"
        if connection[1] in network.switches:
            new_connections[c][1]="s_"+str(connection[1])
        elif connection[1] in network.host_ids:
            new_connections[c][1]="h_"+str(connection[1])
        else:
            new_connections[c][1]="h_client"
    return new_connections

def formalize_connections(network):
    """
    Prepare connections for printing to JSON
    """

    links=list()
    connections=formalize_connection_names(network)
    for c, connection in enumerate(connections):
        if connection[0][0]=="h":
            links.append([str(connection[0]), str(connection[1])+"-p"+str(network.connection_ports[c][1])])
        elif connection[1][0]=="h":
            links.append([str(connection[0])+"-p"+str(network.connection_ports[c][0]), str(connection[1])])
        else:
            links.append([str(connection[0])+"-p"+str(network.connection_ports[c][0]), str(connection[1])+"-p"+str(network.connection_ports[c][1])])
    return links

def write_topology_file(network):
    """
    write topology.json for network
    """
    links=formalize_connections(network)
    switches_formal= formalize_switches(network.switches)
    hosts=  make_host_data(network.host_ids)
    topo_dict=dict(hosts=hosts, switches= switches_formal, links= links)
    with open(network.folder+"/topology.json", "w+") as f:
        json.dump(topo_dict, f, sort_keys=False, indent=4)

def make_rewrite_entry(range, ip):
    """
    Make single No_hop_rewrite table entry
    """
    table_entry = dict({
        "table":"ThisIngress.No_hop_lookup",
        "match":{
            "hdr.dht.group_id": 1,
            "hdr.dht.id": (int(range[0]), int(range[1]))
            },
        "priority": 1,
        "action_name":"ThisIngress.dht_rewrite",
        "action_params":{"dht_address": ip}
        })
    return table_entry
def make_rewrite_table(network, hosts):
    """
    Generate rewrite table for no-hop_rewrite rewrite switch
    """
    rewrite_table=[]
    for h in network.host_ids:
        for f_h in hosts:
            if str(h) in f_h:
                ip= hosts[f_h]["ip"].split("/")[0]
                break
        else:
            raise ValueError("Could not find ", h ," in ", str(hosts))
        for r in network.host_range(h):
            rewrite_table.append(make_rewrite_entry(r, ip))
    #TODO test
    return rewrite_table

def write_build_files(network):
    """
    Generate and write all build files for system
    """
    hosts= make_host_data(network.host_ids)
    switch_lpm_tables=make_ip_lpm_table(network, hosts)

    if network.type=="forward":
        switch_no_hop_tables=make_no_hop_tables(network)
        for s, switch in enumerate(network.switches):
            write_switch_json(switch_no_hop_tables[switch]+switch_lpm_tables[s], switch, network)
        for s, switch in enumerate(network.switches):
            print (switch, len(switch_no_hop_tables[switch]))
    else:
        for s, switch in enumerate(network.switches):
            if switch ==network.rewrite_switch:
                write_switch_json(make_rewrite_table(network, hosts) + switch_lpm_tables[s], switch, network)
            else:
                write_switch_json(switch_lpm_tables[s], switch, network)
    write_topology_file(network)
    with open(network.folder+"/Makefile", "w+") as f:
        lines=["BMV2_SWITCH_EXE = simple_switch_grpc \n",
        "TOPO = ./topology.json \n",
        "source = "+network.compiled_p4_program_path+".p4\n",
        "include ../../utils/Makefile \n" ]
        f.writelines(lines)

def write_switch_json(table, switch, network):
    """
    Write switch info and table to to json
    """
    topo_dict=dict({
                    "target":"bmv2",
                    "bmv2_json": network.compiled_p4_program_path+".json",
                    "p4info": network.compiled_p4_program_path+".p4.p4info.txt",
                    "table_entries": table})

    try:
        os.mkdir(network.folder+"/build/")
    except FileExistsError:
        pass

    with open(network.folder+"/build/"+switch+"P4runtime.json", "w+") as f:
        json.dump(topo_dict, f, sort_keys=True, indent=4)
def make_host_entry(ip_count):
    """
    Generrate JSON entry for host for topology.json
    """
    entry=dict()
    entry["ip"]="10.0."+str(ip_count)+"."+str(ip_count)+"/24"
    entry["mac"]="08:00:00:00:0"+str(ip_count)+":"+str(ip_count)+str(ip_count)
    entry["commands"]=["route add default gw 10.0."+str(ip_count)+"."+str(ip_count)+"0  dev eth0",
    "arp -i eth0 -s 10.0."+str(ip_count)+"."+str(ip_count)+"0 08:00:00:00:0"+str(ip_count)+":00"
    ]
    return entry

def make_host_data(host_ids):
    """
    Define host information for topology.json
    """
    ip_count=1
    hosts=dict()
    hosts["h_client"]=make_host_entry(ip_count)
    ip_count+=1
    for i in host_ids:
        hosts["h_"+str(i)]=make_host_entry(ip_count)
        ip_count+=1
    return hosts

def make_ip_lpm_table(network, hosts):
    """
    Generate IPv4 tables
    """
    switch_lpm_tables=[[]  for _ in range(len(network.switches))]
    for s, switch in enumerate(network.switches):
        for h in network.host_ids+ ["client"]:
            path= nx.dijkstra_path(network.g, switch, h)
            switch_lpm_tables[s].append(make_lpm_entry(switch,s, path[1], network.connections, network.connection_ports, network.switches, hosts["h_"+str(h)]))
    return switch_lpm_tables

def make_lpm_entry(switch,s, next_c, connections, connection_ports, switches, host):
    """
    Make single IPv4 lpm table entry
    """
    for c, connection in enumerate(connections):
        if switch==connection[0] and next_c==connection[1]:
            port=connection_ports[c][0]
            break

        if switch==connection[1] and next_c==connection[0]:
            port=connection_ports[c][1]
            break
    try:
        next_c_spot=find_spot(next_c, switches)
    except ValueError:
        entry={
            "action_name": "ThisIngress.ipv4_forward",
            "action_params": {
                "dstAddr": host["mac"],
                "port": port
            },
            "match": {
                "hdr.ipv4.dstAddr": [
                    host["ip"][0:-3],
                    32
                ]
            },
            "table": "ThisIngress.ipv4_lpm"
        }
        return entry

    entry={
        "action_name": "ThisIngress.ipv4_forward",
        "action_params": {
            "dstAddr": "08:00:00:00:01:"+str(next_c_spot)+str(next_c_spot),
            "port": port
        },
        "match": {
            "hdr.ipv4.dstAddr": [
                str(host["ip"])[0:-3],
                32
            ]
        },
        "table": "ThisIngress.ipv4_lpm"
    }
    return entry

def find_spot(entry, list):
    """
    return index of entry in list
    """
    for s, spot in enumerate(list):
        if entry==spot:
            return s
    else:
        raise ValueError("could not find entry: "+ str(entry)+ " in list: "+ str(list))
